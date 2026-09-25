"""
Unit tests for Escalation Agent.
"""

import pytest
from agents.escalation_agent import EscalationResult, evaluate_escalation


def test_escalation_security_exposure():
    ticket = {
        "id": "T006",
        "subject": "Accidentally committed our secret key to a public GitHub repo",
        "body": "sk_live_... was committed to a public repository.",
        "urgency": "critical",
    }
    result = evaluate_escalation(ticket)
    assert result.escalate is True
    assert "security" in result.escalation_reason.lower() or "secret" in result.escalation_reason.lower()


def test_escalation_payout_hold():
    ticket = {
        "id": "T004",
        "subject": "Connected account payouts stuck in pending for 2 weeks",
        "body": "Funds aren't releasing. Affecting their livelihood.",
        "urgency": "critical",
    }
    result = evaluate_escalation(ticket)
    assert result.escalate is True
    assert "payout" in result.escalation_reason.lower() or "seller" in result.escalation_reason.lower()


def test_escalation_radar_high_value():
    ticket = {
        "id": "T010",
        "subject": "Radar flagged a legitimate high-value customer as fraud",
        "body": "Enterprise customer had a $12,000 charge blocked by Radar.",
        "urgency": "high",
    }
    result = evaluate_escalation(ticket)
    assert result.escalate is True
    assert "radar" in result.escalation_reason.lower() or "fraud" in result.escalation_reason.lower() or "revenue" in result.escalation_reason.lower()


def test_no_escalation_for_standard_docs():
    ticket = {
        "id": "T003",
        "subject": "How do I test webhooks locally?",
        "body": "What's the recommended way to receive webhook events on localhost?",
        "urgency": "low",
    }
    result = evaluate_escalation(ticket)
    assert result.escalate is False
