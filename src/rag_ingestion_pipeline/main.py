import logging
from uuid import uuid4
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Literal
from sqlalchemy import text

from rag_ingestion_pipeline.chunking import fixed_size_chunk
from rag_ingestion_pipeline.database import create_tables, engine, save_chunks
from rag_ingestion_pipeline.embeddings import generate_embedding
from rag_ingestion_pipeline.ingestion import extract_document, validate_upload
from rag_ingestion_pipeline.retrieval import hybrid_search
from rag_ingestion_pipeline.reranking import rerank_chunks
from rag_ingestion_pipeline.generation import generate_grounded_answer
from rag_ingestion_pipeline.knowledge_base import initialize_knowledge_base


app = FastAPI(title="PowerAssist")

# Configure structured application logging.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger("powerassist")

# Create the database tables when the application starts.
create_tables()

# Index the fixed FAQ only if it has not already been indexed.
knowledge_base_status = initialize_knowledge_base()
print(f"Knowledge base initialization: {knowledge_base_status}")


class AskRequest(BaseModel):
    """Represent a question about a specific uploaded document."""

    # Store the user's question.
    question: str

    # Store the document that the question should search.
    document_id: str


class AgentChatRequest(BaseModel):
    """Represent a message sent to the PowerAssist agent."""

    message: str = Field(min_length=1, max_length=2000)


class PredictRequest(BaseModel):
    watts: float = Field(gt=0, le=1_000_000)
    hours: float = Field(gt=0, le=24)


class LookupRequest(BaseModel):
    lookup_type: Literal["state", "tariff"]
    state: str | None = None
    disco_id: str | None = None
    tariff_class: str | None = None
    band: str | None = None



@app.post("/lookup")
def lookup_electricity(request: LookupRequest):
    with engine.connect() as connection:
        if request.lookup_type == "state":
            if not request.state or not request.state.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Provide a state or area to look up.",
                )

            query = text("""
                SELECT
                    s."State_or_Area",
                    s."DisCo_ID",
                    s."Full_Name",
                    t."Tariff_Class",
                    t."Band",
                    t."Rate_NGN_per_kWh",
                    t."Min_Hours_Per_Day"
                FROM state_coverage AS s
                JOIN electricity_tariffs AS t
                    ON s."DisCo_ID" = t."DisCo_ID"
                WHERE LOWER(s."State_or_Area") LIKE LOWER(:state)
                ORDER BY t."Tariff_Class"
                LIMIT 50
            """)

            rows = connection.execute(
                query,
                {"state": f"%{request.state.strip()}%"},
            ).mappings().all()


        else:
            if not request.disco_id or not request.disco_id.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Provide a DisCo ID to look up tariffs.",
                )

            query = text("""
                SELECT "DisCo_ID", "Tariff_Class", "Band",
                       "Rate_NGN_per_kWh", "Min_Hours_Per_Day"
                FROM electricity_tariffs
                WHERE UPPER("DisCo_ID") = UPPER(:disco_id)
                  AND (
                      :tariff_class IS NULL
                      OR LOWER("Tariff_Class") = LOWER(:tariff_class)
                  )
                  AND (
                      :band IS NULL
                      OR UPPER("Band") = UPPER(:band)
                  )
                ORDER BY "Tariff_Class"
                LIMIT 50
            """)

            rows = connection.execute(
                query,
                {
                    "disco_id": request.disco_id.strip(),
                    "tariff_class": request.tariff_class,
                    "band": request.band,
                },
            ).mappings().all()

    return {
        "lookup_type": request.lookup_type,
        "count": len(rows),
        "results": [dict(row) for row in rows],
    }



@app.post("/predict")
def predict_energy(request: PredictRequest):
    if request.watts <= 0 or request.hours <= 0:
        raise HTTPException(
            status_code=400,
            detail="Watts and hours must be greater than zero.",
        )

    energy_kwh = request.watts * request.hours / 1000

    return {
        "watts": request.watts,
        "hours": request.hours,
        "energy_kwh": round(energy_kwh, 3),
        "unit": "kWh",
    }


@app.get("/")
def root():
    return {"message": "RAG ingestion pipeline is running"}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    # Read the uploaded document into memory.
    content = await file.read()

    try:
        # Validate the uploaded file before processing it.
        validate_upload(file, len(content))

        # Generate a unique ID for the uploaded document.
        document_id = str(uuid4())

        # Extract text while preserving page numbers.
        pages = extract_document(content, file.filename or "")

        # Create fixed-size chunks with 50-character overlap.
        chunks = fixed_size_chunk(
            document_id=document_id,
            pages=pages,
            chunk_size=500,
            overlap=50,
        )

        # Reject documents that contain no usable text.
        if not chunks:
            raise ValueError(
                "The uploaded document is empty or contains no usable text."
            )

        # Generate an embedding for every chunk.
        embeddings = [
            generate_embedding(chunk.text)
            for chunk in chunks
        ]

        # Store the chunks, metadata, and embeddings in PostgreSQL.
        save_chunks(chunks, embeddings)

    except ValueError as error:
        # Return validation and processing errors as a client error.
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return {
        "filename": file.filename,
        "document_id": document_id,
        "chunks_created": len(chunks),
        "embeddings_generated": len(embeddings),
        "stored": len(chunks),
        "message": "Document successfully ingested",
    }


@app.post("/ask")
def ask_question(request: AskRequest):
    """Retrieve evidence and generate a grounded answer."""

    # Generate an embedding for the user's question.
    query_embedding = generate_embedding(request.question)

    # Connect to PostgreSQL for retrieval.
    with Session(engine) as session:
        # Retrieve a larger candidate pool using hybrid search.
        hybrid_results = hybrid_search(
            session,
            request.question,
            query_embedding,
            top_k=10,
            document_id=request.document_id,
        )

    # Extract the retrieved chunks from the hybrid results.
    candidate_chunks = [
        chunk
        for chunk, _ in hybrid_results
    ]

    # Rerank the candidate chunks using the cross-encoder.
    reranked_results = rerank_chunks(
        request.question,
        candidate_chunks,
        top_k=5,
    )

    # Refuse to answer when no evidence was retrieved.
    if not reranked_results:
        return {
            "question": request.question,
            "answer": (
                "I could not find enough information in the uploaded "
                "documents to answer this question."
            ),
            "sources": [],
        }

    # Build citation-labelled context for the language model.
    context_parts = []

    for chunk, _ in reranked_results:
        # Build a page-aware citation for documents that have page numbers.
        if chunk.page_number is not None:
            citation = (
                f"[Page {chunk.page_number}, "
                f"Chunk {chunk.chunk_index}]"
            )
        else:
            # Use only the chunk number for documents without pages, such as TXT.
            citation = f"[Chunk {chunk.chunk_index}]"

        # Add the citation before the chunk so the model can reference it.
        context_parts.append(
            f"{citation}\n"
            f"{chunk.text}"
        )

    # Combine all retrieved chunks into one context.
    context = "\n\n".join(context_parts)

    # Generate an answer grounded only in the retrieved evidence.
    answer = generate_grounded_answer(
        question=request.question,
        context=context,
    )

    # Return the grounded answer and supporting sources.
    return {
        "question": request.question,
        "answer": answer,
        "sources": [
            {
                "document_id": chunk.document_id,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
            }
            for chunk, _ in reranked_results
        ],
    }


@app.get("/ui", response_class=HTMLResponse)
def upload_ui():
    # Locate the HTML upload page in the project templates directory.
    template_path = Path("templates/upload.html")

    # Return the upload page to the browser.
    return template_path.read_text(encoding="utf-8")


@app.post("/agent/chat")
async def agent_chat(request: AgentChatRequest):
    """Send a message to the PowerAssist tool-using agent."""
    if not request.message.strip():
        raise HTTPException(
            status_code=422,
            detail="Please enter a question containing at least one non-space character.",
        )
    from rag_ingestion_pipeline.agent import agent

    try:
        result = await agent.run(request.message)
        logger.info("Agent request completed successfully")
        return {
            "message": request.message,
            "answer": result.text,
        }
    except Exception as exc:
        logger.exception("Agent request failed")
        raise HTTPException(
            status_code=500,
            detail="PowerAssist could not process your request. Please try again.",
        )