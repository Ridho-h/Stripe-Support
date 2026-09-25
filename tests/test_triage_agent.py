"""
Unit tests for Triage Agent.
"""

import pytest
from agents.triage_agent import (
    TRIAGE_SYSTEM_PROMPT,
    VALID_CATEGORIES,
    VALID_URGENCIES,
    TriageResult,
    _heuristic_triage,
    triage_ticket,
)


def test_valid_categories_count():
    assert len(VALID_CATEGORIES) == 10
    assert "webhooks" in VALID_CATEGORIES
    assert "radar_fraud" in VALID_CATEGORIES
    assert "auth_keys" in VALID_CATEGORIES


def test_valid_urgencies_count():
    assert len(VALID_URGENCIES) == 4
    assert VALID_URGENCIES == ["low", "medium", "high", "critical"]


def test_triage_webhook_ticket():
    ticket = {
        "id": "T001",
        "subject": "Webhook signature verification keeps failing",
        "body": "No signatures found matching the expected signature for payload.",
    }
    result = triage_ticket(ticket)
    assert result.category == "webhooks"
    assert result.urgency in ["medium", "high", "critical"]
    assert len(result.reasoning) > 10
    assert 0.0 <= result.confidence <= 1.0


def test_triage_secret_key_ticket():
    ticket = {
        "id": "T006",
        "subject": "Accidentally committed our secret key to a public GitHub repo",
        "body": "sk_live_... was committed to public repository. Please advise immediately.",
    }
    result = triage_ticket(ticket)
    assert result.category == "auth_keys"
    assert result.urgency == "critical"


def test_triage_dispute_ticket():
    ticket = {
        "id": "T008",
        "subject": "Dispute filed as fraudulent but we have delivery proof",
        "body": "A customer disputed a $340 charge claiming they never received the product.",
    }
    result = triage_ticket(ticket)
    assert result.category == "refunds_disputes"
    assert result.urgency in ["high", "medium"]


def test_triage_general_inquiry():
    ticket = {
        "id": "T021",
        "subject": "Simple question: does Stripe support Apple Pay?",
        "body": "Considering switching to Stripe from a competitor.",
    }
    result = triage_ticket(ticket)
    assert result.category == "general"
    assert result.urgency == "low"
