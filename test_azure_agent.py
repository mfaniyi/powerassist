from dotenv import load_dotenv
import os
from agent_framework.openai import OpenAIChatClient

load_dotenv()

client = OpenAIChatClient(
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)

print("Client:", type(client).__name__)
print("Deployment configured:", bool(os.getenv("AZURE_OPENAI_DEPLOYMENT")))
print("Endpoint configured:", bool(os.getenv("AZURE_OPENAI_ENDPOINT")))
