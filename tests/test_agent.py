
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


def test_agent_rejects_out_of_scope_request():
    """Verify unrelated requests are refused without calling the agent."""
    from unittest.mock import patch

    with patch(
        "rag_ingestion_pipeline.agent.agent.run"
    ) as mock_run:
        response = client.post(
            "/agent/chat",
            json={"message": "Who won the football match?"},
        )

    assert response.status_code == 200
    assert "only help with Nigerian electricity" in (
        response.json()["answer"]
    )
    mock_run.assert_not_called()