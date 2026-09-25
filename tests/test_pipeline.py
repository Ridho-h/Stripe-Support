"""
Integration tests for Orchestrator Pipeline.
"""

import json
import os
import pytest
from orchestrator.pipeline import run_ticket_pipeline
from mcp_servers.ticket_server.server import get_ticket


def test_pipeline_single_ticket():
    ticket = get_ticket("T001")
    result = run_ticket_pipeline(ticket)

    assert result["ticket_id"] == "T001"
    assert len(result["stages"]) == 4
    
    # Check each stage execution
    stage_names = [s["agent"] for s in result["stages"]]
    assert stage_names == [
        "Triage Agent",
        "Retrieval Agent",
        "Drafting Agent",
        "Escalation Agent",
    ]

    for s in result["stages"]:
        assert s["status"] == "completed"
        assert "latency_ms" in s
        assert "timestamp" in s
        assert "output" in s
        assert "reasoning" in s

    pred = result["prediction"]
    assert pred["category"] == "webhooks"
    assert pred["urgency"] in ["medium", "high", "critical"]
    assert len(pred["retrieved_doc_topics"]) == 3
    assert pred["escalate"] is False
    assert len(pred["draft_reply"]) > 20


def test_pipeline_escalated_ticket():
    ticket = get_ticket("T006")  # Secret key exposure
    result = run_ticket_pipeline(ticket)
    pred = result["prediction"]
    assert pred["category"] == "auth_keys"
    assert pred["urgency"] == "critical"
    assert pred["escalate"] is True
