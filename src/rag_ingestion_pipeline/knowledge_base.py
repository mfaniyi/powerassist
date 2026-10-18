from pathlib import Path

from sqlalchemy.orm import Session

from rag_ingestion_pipeline.chunking import fixed_size_chunk
from rag_ingestion_pipeline.database import DocumentChunk, engine, save_chunks
from rag_ingestion_pipeline.embeddings import generate_embedding
from rag_ingestion_pipeline.ingestion import extract_document


FAQ_DOCUMENT_ID = "nerc-nigeria-faq"
FAQ_PATH = Path(__file__).resolve().parents[2] / "data" / "NERC_Nigeria_FAQ.pdf"


def initialize_knowledge_base() -> dict:
    """Index the fixed NERC FAQ PDF once, reusing existing chunks if present."""

    with Session(engine) as session:
        existing_count = (
            session.query(DocumentChunk)
            .filter(DocumentChunk.document_id == FAQ_DOCUMENT_ID)
            .count()
        )

    if existing_count:
        return {
            "status": "already_indexed",
            "document_id": FAQ_DOCUMENT_ID,
            "chunks": existing_count,
        }

    if not FAQ_PATH.exists():
        raise FileNotFoundError(f"FAQ document not found: {FAQ_PATH}")

    pages = extract_document(FAQ_PATH.read_bytes(), FAQ_PATH.name)
    chunks = fixed_size_chunk(
        document_id=FAQ_DOCUMENT_ID,
        pages=pages,
        chunk_size=500,
        overlap=50,
    )

    if not chunks:
        raise ValueError("The FAQ PDF contains no extractable text.")

    embeddings = [generate_embedding(chunk.text) for chunk in chunks]
    save_chunks(chunks, embeddings)

    return {
        "status": "indexed",
        "document_id": FAQ_DOCUMENT_ID,
        "chunks": len(chunks),
    }
