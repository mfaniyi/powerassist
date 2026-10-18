
from fastapi.testclient import TestClient

from rag_ingestion_pipeline.main import app


client = TestClient(app)


def test_agent_rejects_whitespace_only_message():
    """Verify that whitespace-only messages are rejected."""
    response = client.post(
        "/agent/chat",
        json={"message": "   "},
    )

    assert response.status_code == 422
    assert "non-space character" in response.json()["detail"]


def test_agent_rejects_empty_message():
    """Verify that empty messages are rejected."""
    response = client.post(
        "/agent/chat",
        json={"message": ""},
    )

    assert response.status_code == 422
