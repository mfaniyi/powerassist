# PowerAssist — Electricity Information and Energy Estimation Agent

PowerAssist is a FastAPI-based, tool-using AI agent that helps users understand electricity usage, estimate appliance energy consumption, and retrieve information about Nigeria’s electricity sector.

Built on a Retrieval-Augmented Generation (RAG) pipeline, PowerAssist provides three core tools: **Ask**, **Predict**, and **Lookup**. It includes a web interface, document ingestion, security guardrails, automated tests, Azure Key Vault integration, managed identity, and Application Insights monitoring.

## Live Application

- **Web interface:** https://powerassist-api.grayplant-1453df5e.eastus.azurecontainerapps.io/ui
- **API root:** https://powerassist-api.grayplant-1453df5e.eastus.azurecontainerapps.io/
- **API documentation:** https://powerassist-api.grayplant-1453df5e.eastus.azurecontainerapps.io/docs

The deployed `v4` image was built and pushed successfully to Azure Container Registry. The `/ui` endpoint was verified to return HTTP 200 with `text/html` content, and the updated interface was visually checked.

## Features

- **Ask:** Answers questions using the RAG knowledge base.
- **Predict:** Estimates electricity consumption in kilowatt-hours (kWh) from appliance power and usage duration.
- **Lookup:** Retrieves structured electricity-sector information.
- **Document ingestion:** Supports PDF and TXT uploads for knowledge-base ingestion.
- **Web interface:** Provides an HTML frontend for interacting with PowerAssist.
- **Agent endpoint:** Exposes a tool-using agent through `/agent/chat`.
- **Guardrails:** Validates inputs, restricts tool usage, and limits agent tool calls.
- **Secrets management:** Supports Azure Key Vault and environment-based local development.
- **Monitoring:** Integrates Azure Application Insights and Azure Monitor telemetry.
- **Automated testing:** Uses pytest and GitHub Actions CI.

## Architecture

```text
User
 |
 v
PowerAssist HTML Interface / API
 |
 v
FastAPI Application
 |
 +--> /ask -------> RAG retrieval and answer generation
 |
 +--> /predict ---> Energy consumption calculation
 |
 +--> /lookup ----> Structured electricity information
 |
 +--> /upload ----> Document ingestion
 |
 +--> /agent/chat -> Tool-using AI agent
                       |
                       +--> Ask
                       +--> Predict
                       +--> Lookup

PostgreSQL + pgvector --> RAG storage
Azure Key Vault -------> Secret management
Managed Identity ------> Azure authentication
Application Insights --> Monitoring and telemetry
```

## Technology Stack

- Python and FastAPI
- Microsoft Agent Framework
- Azure OpenAI
- Azure Key Vault and Azure Identity
- Azure Container Apps and Azure Container Registry
- Azure Application Insights and OpenTelemetry
- PostgreSQL and pgvector
- SQLAlchemy and Pydantic
- `uv` dependency management
- Docker
- pytest and GitHub Actions

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Application health/message endpoint |
| GET | `/ui` | Open the HTML interface |
| POST | `/ask` | Query the RAG knowledge base |
| POST | `/predict` | Estimate appliance energy consumption |
| POST | `/lookup` | Retrieve structured electricity information |
| POST | `/upload` | Upload a supported document |
| POST | `/agent/chat` | Interact with the tool-using agent |

Use `/docs` to inspect the actual request schemas and try the API endpoints.

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
│   └── upload.html
├── Dockerfile
├── pyproject.toml
├── uv.lock
└── README.md
```

The repository may contain additional modules or files as development progresses. The `.env` file is local configuration and must not be committed.

## Local Setup

### 1. Install dependencies

From the project root:

```bash
uv sync --locked --dev
```

### 2. Start PostgreSQL with pgvector

If the project's local database container does not already exist, create one:

```bash
docker run -d \
  --name rag-postgres \
  -e POSTGRES_USER=raguser \
  -e POSTGRES_PASSWORD=ragpassword \
  -e POSTGRES_DB=powerassist \
  -p 5433:5432 \
  pgvector/pgvector:pg18
```

If the container already exists, reuse it. Confirm that the database, pgvector extension, and connection settings match your local configuration.

### 3. Configure environment variables

Create a `.env` file in the project root. Use the values and variable names required by your environment.

```dotenv
DATABASE_URL=postgresql+psycopg://raguser:YOUR_PASSWORD@localhost:5433/powerassist

AZURE_OPENAI_ENDPOINT=https://YOUR-RESOURCE.services.ai.azure.com
AZURE_OPENAI_CHAT_MODEL=YOUR_DEPLOYMENT_NAME
AZURE_OPENAI_API_KEY=YOUR_LOCAL_API_KEY

APPLICATIONINSIGHTS_CONNECTION_STRING=
```

For local development, the application supports `AZURE_OPENAI_API_KEY` when `KEY_VAULT_URL` is not configured.

Never commit actual credentials, connection strings containing secrets, or the `.env` file.

### 4. Run the application

```bash
uv run uvicorn rag_ingestion_pipeline.main:app --reload
```

Open:

- Web interface: http://127.0.0.1:8000/ui
- API root: http://127.0.0.1:8000/
- Interactive API documentation: http://127.0.0.1:8000/docs

## Example: Energy Estimation

The basic energy calculation is:

```text
Energy (kWh) = Power (Watts) × Usage (Hours) / 1000
```

For a 100-watt appliance operating for five hours:

```text
100 × 5 / 1000 = 0.5 kWh
```

This is an illustrative calculation. Consult `/docs` for the exact JSON fields required by the deployed endpoint.

## Security and Privacy

### Azure Key Vault and managed identity

The application supports retrieving the Azure OpenAI API key through Azure Key Vault using `SecretClient` and `DefaultAzureCredential`.

The Azure configuration includes:

- Key Vault: `powerassist-kv-mfaniyi`
- User-assigned identity: `secure-candidate-identity`
- Required Key Vault role: **Key Vault Secrets User**, assigned at the appropriate vault scope
- Application configuration: `KEY_VAULT_URL` and `AZURE_CLIENT_ID`

The local development path supports an environment-based API key when Key Vault is not configured.

The application has been deployed with the user-assigned identity configuration. A successful agent response has also been observed. For formal assessment evidence, retain the identity role-assignment output and verify the secret retrieval path and relevant Key Vault audit evidence where available.

### Application Insights

The application is configured to initialize Azure Monitor when `APPLICATIONINSIGHTS_CONNECTION_STRING` is supplied.

Telemetry ingestion has previously been observed. Application logs and telemetry should not contain API keys, authorization headers, or unnecessary personal or sensitive information.

### Retention and privacy controls

- Application Insights retention was reported as 90 days during configuration checks.
- A proposed 30-day retention policy has **not been implemented**.
- Request validation and agent tool-call limits are included in the application's security controls.
- Access to Azure resources should follow least-privilege principles.
- Review `docs/SECURITY_AND_PII.md` for implementation details and outstanding verification.

## Testing

Run the automated test suite:

```bash
uv run pytest -q
```

The test suite previously passed with **35 tests** after the managed-identity code change. Re-run the tests whenever code changes are made.

GitHub Actions CI has also passed following earlier fixes. Check the latest workflow run in GitHub when collecting final assessment evidence.

## Azure Deployment

PowerAssist is deployed to Azure Container Apps.

| Resource | Configuration |
|---|---|
| Container App | `powerassist-api` |
| Resource group | `rg-secure-candidate` |
| Container Registry | `securecandidateacr.azurecr.io` |
| Deployed image | `powerassist-api:v4` |
| Key Vault | `powerassist-kv-mfaniyi` |
| Application Insights | `powerassist-insights` |

The `v4` image was successfully built and pushed to Azure Container Registry. The live `/ui` endpoint returned HTTP 200 with an HTML content type, and the interface was confirmed working.

For future deployments, build and push a new image, update the Container App, and verify the health endpoint, `/ui`, agent functionality, identity configuration, and telemetry.

## Current Verification Status

| Area | Status |
|---|---|
| Azure image build and push (`v4`) | Verified |
| Container App update | Completed |
| Live HTML interface | Verified; HTTP 200 |
| Panel colour and footer updates | Visually verified |
| Automated tests | Previously passed; rerun for final evidence |
| Key Vault and managed identity configuration | Configured; retain role-assignment evidence |
| End-to-end Key Vault audit evidence | Further evidence recommended |
| Application Insights telemetry | Ingestion previously observed |
| Effective retention setting | Confirm against the Azure resource |
| 90-day retention policy | Implemented |

## Project Goal

PowerAssist demonstrates how a small tool-using AI agent can combine RAG, structured lookups, energy calculations, input validation, secret management, monitoring, and automated testing in a practical application relevant to Nigeria's electricity sector.
