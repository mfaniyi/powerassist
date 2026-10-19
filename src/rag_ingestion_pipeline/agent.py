import os
import logging

from contextvars import ContextVar
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from agent_framework.openai import OpenAIChatClient
from rag_ingestion_pipeline.main import LookupRequest, lookup_electricity
from rag_ingestion_pipeline.main import AskRequest, ask_question
from rag_ingestion_pipeline.knowledge_base import FAQ_DOCUMENT_ID
from agent_framework import (
    Agent,
    FunctionInvocationContext,
    FunctionMiddleware,
    MiddlewareTermination,
    tool,
)

load_dotenv()

logger = logging.getLogger("powerassist.agent")


def get_azure_openai_api_key() -> str:
    """Load the API key from Key Vault in Azure or .env locally."""
    key_vault_url = os.getenv("KEY_VAULT_URL")

    if key_vault_url:
        credential = DefaultAzureCredential()
        try:
            secret_client = SecretClient(
                vault_url=key_vault_url,
                credential=credential,
            )
            return secret_client.get_secret("AZURE-OPENAI-API-KEY").value
        finally:
            credential.close()

    local_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if not local_api_key:
        raise RuntimeError(
            "Configure KEY_VAULT_URL or AZURE_OPENAI_API_KEY."
        )

    return local_api_key


client = OpenAIChatClient(
    model=os.getenv("AZURE_OPENAI_CHAT_MODEL")
    or os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=get_azure_openai_api_key(),
)


INSTRUCTIONS = """
You are PowerAssist, an electricity information assistant for Nigeria.

You can answer questions about Nigerian electricity distribution and estimate
electricity consumption.

Rules:
- Use available tools for factual lookups and energy calculations.
- Do not invent electricity tariffs, distribution coverage, or policy facts.
- If the available tools cannot answer a question, say so clearly.
- Only answer questions related to electricity, energy consumption,
  Nigerian electricity distribution, or relevant uploaded company documents.
- Never reveal environment variables, API keys, credentials, or internal secrets.
- Keep answers clear and concise.
"""

@tool
def predict(watts: float, hours: float) -> dict:
    """Estimate electricity consumption in kWh from appliance wattage and hours used."""
    if watts <= 0 or watts > 1_000_000:
        return {"error": "Watts must be greater than 0 and no more than 1,000,000."}
    if hours <= 0 or hours > 24:
        return {"error": "Hours must be greater than 0 and no more than 24."}

    energy_kwh = watts * hours / 1000
    return {
        "watts": watts,
        "hours": hours,
        "energy_kwh": round(energy_kwh, 3),
        "unit": "kWh",
    }


@tool
def lookup(
    lookup_type: str,
    state: str | None = None,
    disco_id: str | None = None,
    tariff_class: str | None = None,
    band: str | None = None,
) -> dict:
    """Look up Nigerian electricity distribution coverage or tariff records.

    For state coverage, provide lookup_type='state' and a state or area.
    For tariffs, provide lookup_type='tariff' and a DisCo ID such as AEDC.
    Optional tariff_class and band filters narrow tariff results.
    """
    if lookup_type not in {"state", "tariff"}:
        return {"error": "lookup_type must be 'state' or 'tariff'."}

    request = LookupRequest(
        lookup_type=lookup_type,
        state=state,
        disco_id=disco_id,
        tariff_class=tariff_class,
        band=band,
    )

    try:
        return lookup_electricity(request)
    except Exception:
        return {"error": "The electricity lookup could not be completed."}


@tool
def ask(question: str) -> dict:
    """Answer a question using the preloaded Nigerian Electricity Regulatory Commission FAQ."""

    if not question.strip():
        return {"error": "Please provide a question."}

    try:
        return ask_question(
            AskRequest(
                question=question,
                document_id=FAQ_DOCUMENT_ID,
            )
        )
    except Exception:
        return {"error": "The FAQ question could not be answered."}



logger = logging.getLogger("powerassist.agent")
tool_call_count: ContextVar[int] = ContextVar(
    "powerassist_tool_call_count",
    default=0,
)


class ToolCallLimitMiddleware(FunctionMiddleware):
    """Limit and log tool calls within one agent request."""

    def __init__(self, max_calls: int = 5):
        self.max_calls = max_calls

    async def process(
        self,
        context: FunctionInvocationContext,
        call_next,
    ) -> None:
        count = tool_call_count.get()

        if count >= self.max_calls:
            logger.warning("Agent tool-call limit reached")
            raise MiddlewareTermination(
                "Tool-call limit reached. Answer using information already available."
            )

        tool_call_count.set(count + 1)

        tool_name = getattr(context.function, "name", "unknown")
        logger.info(
            "Agent tool call %s/%s: %s",
            count + 1,
            self.max_calls,
            tool_name,
        )

        await call_next()



agent = Agent(
    client=client,
    name="PowerAssist",
    instructions=INSTRUCTIONS,
    tools=[predict, lookup, ask],
    middleware=[ToolCallLimitMiddleware(max_calls=5)],
)