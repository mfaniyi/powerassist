
from fastapi.testclient import TestClient

from rag_ingestion_pipeline.main import app


client = TestClient(app)


def test_predict_calculates_energy_correctly():
    """Verify energy consumption is calculated in kWh."""
    response = client.post(
        "/predict",
        json={"watts": 100, "hours": 8},
    )

    assert response.status_code == 200
    assert response.json()["energy_kwh"] == 0.8
    assert response.json()["unit"] == "kWh"


def test_predict_rejects_zero_watts():
    """Verify zero watts is rejected."""
    response = client.post(
        "/predict",
        json={"watts": 0, "hours": 8},
    )

    assert response.status_code == 422


def test_predict_rejects_hours_above_24():
    """Verify durations greater than 24 hours are rejected."""
    response = client.post(
        "/predict",
        json={"watts": 100, "hours": 25},
    )

    assert response.status_code == 422
