from fastapi.testclient import TestClient
from rag_ingestion_pipeline.main import app

client = TestClient(app)


def test_lookup_rejects_missing_state():
    """Verify that a state lookup requires a state or area."""
    response = client.post(
        "/lookup",
        json={"lookup_type": "state"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Provide a state or area to look up."


def test_lookup_rejects_missing_disco_id():
    """Verify that a tariff lookup requires a DisCo ID."""
    response = client.post(
        "/lookup",
        json={"lookup_type": "tariff"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Provide a DisCo ID to look up tariffs."
