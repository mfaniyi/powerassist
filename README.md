# PowerAssist — Electricity Information and Energy Estimation Agent

PowerAssist is a FastAPI-based, tool-using AI agent that helps users understand electricity usage, estimate appliance energy consumption, and retrieve information about Nigeria’s electricity sector.

The project builds on a Retrieval-Augmented Generation (RAG) pipeline and includes three core tools: `/ask`, `/predict`, and `/lookup`. It also incorporates security guardrails, automated tests, Azure Key Vault integration, managed identity, and Application Insights monitoring.

## Features

- **Ask:** Answers questions using the RAG knowledge base.
- **Predict:** Estimates electricity consumption in kilowatt-hours (kWh) from appliance power and usage duration.
- **Lookup:** Retrieves structured electricity-sector information.
- **Document ingestion:** Supports PDF and TXT uploads for knowledge-base ingestion.
- **Agent interface:** Provides a web UI and an agent chat endpoint.
- **Guardrails:** Validates inputs, restricts tool usage, and limits agent tool calls.
- **Secrets management:** Supports Azure Key Vault in Azure and environment-based secrets for local development.
- **Monitoring:** Supports Azure Application Insights telemetry.

## Architecture

```text
User
  |
  v
FastAPI Application
  |
  +--> /ask ------> RAG Retrieval and Answer Generation
  |
  +--> /predict --> Energy Consumption Calculation
  |
  +--> /lookup ---> Structured Electricity Information
  |
  +--> /upload ---> Document Ingestion
  |
  +--> /agent/chat -> Tool-Using Agent
                         |
                         +--> Ask
                         +--> Predict
                         +--> Lookup

PostgreSQL + pgvector --> RAG Storage
Azure Key Vault -------> Application Secrets
Application Insights --> Monitoring and Telemetry
```

## Technology Stack

- Python and FastAPI
- Microsoft Agent Framework
- Azure OpenAI
- Azure Key Vault and Azure Identity
- Azure Application Insights and OpenTelemetry
- PostgreSQL and pgvector
- SQLAlchemy
- Pydantic
- `uv` for dependency management
- Docker for local database development
- Pytest for automated testing

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Application health/message endpoint |
| POST | `/ask` | Ask a question against the RAG knowledge base |
| POST | `/predict` | Estimate appliance energy consumption |
| POST | `/lookup` | Retrieve structured electricity-sector information |
| POST | `/upload` | Upload a supported document |
| GET | `/ui` | Open the web interface |
| POST | `/agent/chat` | Interact with the tool-using agent |

Consult the request models in `src/rag_ingestion_pipeline/main.py` for the required JSON fields and validation rules.

## Project Structure

```text
powerassist/
├── .github/
│   └── workflows/
│       └── ci.yml
├── docs/
│   └── SECURITY_AND_PII.md
├── src/
│   └── rag_ingestion_pipeline/
│       ├── agent.py
│       ├── main.py
│       ├── database.py
│       ├── ingestion.py
│       ├── chunking.py
│       ├── embeddings.py
│       ├── retrieval.py
│       ├── reranking.py
│       └── generation.py
├── tests/
├── templates/
├── .env
├── pyproject.toml
├── uv.lock
└── README.md
```

The exact contents of the repository may evolve as the project develops.

## Prerequisites

- Python version supported by `pyproject.toml`
- `uv`
- Docker, for a local PostgreSQL + pgvector database
- Azure OpenAI deployment and credentials
- An Azure Key Vault and authorized identity for Azure secret retrieval
- An Application Insights resource for Azure monitoring

## Local Setup

### 1. Install dependencies

From the project root, run:

```bash
uv sync --locked --dev
```

### 2. Start PostgreSQL with pgvector

If you do not already have the project's local PostgreSQL container running, you can create one with:

```bash
docker run -d \
  --name rag-postgres \
  -e POSTGRES_USER=raguser \
  -e POSTGRES_PASSWORD=ragpassword \
  -e POSTGRES_DB=powerassist \
  -p 5433:5432 \
  pgvector/pgvector:pg18
```

If the container already exists, reuse it rather than creating a duplicate.

Ensure the database exists, the pgvector extension is enabled, and the connection details match your local configuration.

### 3. Configure environment variables

Create a local `.env` file in the project root. Use the variable names expected by the application.

```dotenv
DATABASE_URL=postgresql+psycopg://raguser:YOUR_PASSWORD@localhost:5433/powerassist

AZURE_OPENAI_ENDPOINT=https://YOUR-RESOURCE.services.ai.azure.com
AZURE_OPENAI_CHAT_MODEL=YOUR_DEPLOYMENT_NAME
AZURE_OPENAI_API_KEY=YOUR_LOCAL_API_KEY

APPLICATIONINSIGHTS_CONNECTION_STRING=
```

For local development, `AZURE_OPENAI_API_KEY` is the fallback when `KEY_VAULT_URL` is not configured. Use real credentials only in your local environment; never commit them.

The application also supports `KEY_VAULT_URL` for retrieving the Azure OpenAI API key from Key Vault. Azure deployments should use the intended managed identity and appropriate permissions.

Do not commit `.env` or any file containing secrets.

### 4. Run the application

```bash
uv run uvicorn rag_ingestion_pipeline.main:app --reload
```

Open the local application at:

- API root: `http://127.0.0.1:8000/`
- Web interface: `http://127.0.0.1:8000/ui`
- API documentation: `http://127.0.0.1:8000/docs`

## Example Usage

The precise request fields depend on the Pydantic request models in `main.py`.

### Energy estimation

```json
{
  "watts": 100,
  "hours": 5
}
```

For a 100-watt appliance operating for five hours:

`Energy (kWh) = (Watts × Hours) / 1000`

The estimated consumption is **0.5 kWh**. This is an illustrative calculation, not a claim about the endpoint's exact JSON schema.

### Ask and lookup

Use the interactive API documentation at `/docs` to inspect the request schemas and try `/ask` and `/lookup` with valid sample inputs.

## Security and Privacy

PowerAssist includes security controls intended to protect application credentials, validate requests, and reduce sensitive information in telemetry.

### Azure Key Vault and managed identity

- The application supports retrieving the Azure OpenAI API key through Azure Key Vault's `SecretClient`.
- `KEY_VAULT_URL` identifies the vault used by the application.
- `DefaultAzureCredential` provides the Azure authentication path.
- The intended managed identity must have the **Key Vault Secrets User** role at the appropriate scope.
- Local development can use an API key from `.env` when Key Vault is not configured.

The code and permissions are configured, but deployed runtime retrieval must be verified before claiming end-to-end success.

### Application Insights

The application initializes Azure Monitor through `configure_azure_monitor` when `APPLICATIONINSIGHTS_CONNECTION_STRING` is configured.

Avoid logging API keys, authorization headers, complete request bodies, or sensitive tool arguments. Restrict access to monitoring data and review telemetry for unintended personal information.

### Retention

Application Insights is configured for 90-day telemetry retention, subject to verification of the effective resource setting. A shorter 30-day policy has been proposed but is **not implemented**.

### Additional controls

- Request validation and tool-level checks
- Agent tool-call limits
- Local secret exclusion from version control
- Least-privilege access to Azure resources
- Security and privacy documentation in `docs/SECURITY_AND_PII.md`

See [docs/SECURITY_AND_PII.md](docs/SECURITY_AND_PII.md) for implementation status and outstanding verification.

## Testing

Run the automated test suite:

```bash
uv run pytest -q
```

The suite has previously passed with **35 tests**. Run it again after making changes to confirm the current result.

The GitHub Actions workflow in `.github/workflows/ci.yml` runs the automated tests in CI. A successful local test run does not replace verification of the latest GitHub Actions run.

## Deployment

PowerAssist is designed to run locally during development and can be deployed to Azure Container Apps.

The Azure deployment uses:

- Azure Container Apps to host the API
- Azure Key Vault for secret storage
- Managed identity for authorized Key Vault access
- Application Insights for telemetry
- Azure-hosted database infrastructure for persistent storage

Before a deployment is considered verified, confirm that the deployed image contains the latest code, the correct managed identity is selected, Key Vault retrieval succeeds, the API starts correctly, and telemetry is received without exposing secrets.

## Current Security-Hardening Status

| Area | Status |
|---|---|
| Key Vault retrieval code | Implemented; local tests passed |
| Key Vault and managed identity permissions | Configured; runtime verification required |
| Deployed Key Vault secret retrieval | Pending verification |
| Application Insights integration | Configured; ingestion observed |
| Effective telemetry retention | Verify the Azure resource setting |
| 30-day retention policy | Proposed, not implemented |
| Automated tests | Previously passed; rerun after changes |

## Project Goal

PowerAssist demonstrates how a small tool-using AI agent can combine RAG, structured lookups, energy calculations, input validation, secrets management, monitoring, and automated testing in a practical application relevant to Nigeria's electricity sector.
