from unittest.mock import patch

from rag_ingestion_pipeline.agent import ask, lookup, predict
from types import SimpleNamespace

import pytest
from agent_framework import MiddlewareTermination
from rag_ingestion_pipeline.agent import (ToolCallLimitMiddleware, tool_call_count)


def test_predict_tool_calculates_energy():
    """Evaluate the prediction tool."""
    result = predict(watts=100, hours=8)

    assert result["energy_kwh"] == 0.8
    assert result["unit"] == "kWh"


def test_predict_tool_rejects_invalid_watts():
    """Evaluate prediction guardrails."""
    result = predict(watts=0, hours=8)

    assert "error" in result


def test_predict_tool_rejects_hours_above_24():
    """Prevent unrealistic daily usage durations."""
    result = predict(watts=100, hours=25)

    assert "error" in result


def test_lookup_tool_rejects_invalid_lookup_type():
    """Reject unsupported lookup requests."""
    result = lookup(lookup_type="invalid")

    assert "error" in result


def test_lookup_tool_handles_database_failure():
    """Return a safe message if the lookup fails."""
    with patch(
        "rag_ingestion_pipeline.agent.lookup_electricity",
        side_effect=Exception("Database details must not leak"),
    ):
        result = lookup(lookup_type="state", state="Lagos")

    assert "error" in result
    assert "Database details must not leak" not in str(result)


def test_ask_tool_rejects_empty_question():
    """Reject empty FAQ questions."""
    result = ask(question="   ")

    assert "error" in result


def test_ask_tool_handles_retrieval_failure():
    """Return a safe message if the FAQ tool fails."""
    with patch(
        "rag_ingestion_pipeline.agent.ask_question",
        side_effect=Exception("Internal details must not leak"),
    ):
        result = ask(question="What is electricity regulation?")

    assert "error" in result
    assert "Internal details must not leak" not in str(result)


@pytest.mark.anyio
async def test_tool_call_limit_stops_sixth_call():
    middleware = ToolCallLimitMiddleware(max_calls=5)
    token = tool_call_count.set(0)
    calls_executed = 0

    async def call_next():
        nonlocal calls_executed
        calls_executed += 1

    context = SimpleNamespace(
        function=SimpleNamespace(name="predict")
    )

    try:
        for _ in range(5):
            await middleware.process(context, call_next)

        with pytest.raises(MiddlewareTermination):
            await middleware.process(context, call_next)

        assert calls_executed == 5
    finally:
        tool_call_count.reset(token)
