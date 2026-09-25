"""
Unit tests for Ticket MCP Server.
"""

import os
import pytest
from mcp_servers.ticket_server.db import (
    DEFAULT_DB_PATH,
    get_ticket as db_get_ticket,
    init_db,
    list_tickets as db_list_tickets,
    update_ticket as db_update_ticket,
)
from mcp_servers.ticket_server.server import get_ticket, list_tickets, update_ticket


def test_init_db():
    init_db()
    tickets = db_list_tickets()
    assert len(tickets) == 30


def test_get_ticket_existing():
    t = get_ticket("T001")
    assert t["id"] == "T001"
    assert "Webhook" in t["subject"]
    assert t["category"] == "webhooks"
    assert isinstance(t["escalate"], bool)


def test_get_ticket_nonexistent():
    res = get_ticket("T999")
    assert "error" in res


def test_list_tickets_all():
    tickets = list_tickets()
    assert len(tickets) >= 30


def test_list_tickets_filter_urgency():
    criticals = list_tickets(urgency="critical")
    assert len(criticals) > 0
    assert all(t["urgency"] == "critical" for t in criticals)


def test_list_tickets_filter_category():
    webhooks = list_tickets(category="webhooks")
    assert len(webhooks) > 0
    assert all(t["category"] == "webhooks" for t in webhooks)


def test_update_ticket():
    t = get_ticket("T001")
    orig_status = t.get("status", "open")
    
    updated = update_ticket("T001", {"status": "in_review", "predicted_category": "webhooks"})
    assert updated["status"] == "in_review"
    assert updated["predicted_category"] == "webhooks"

    # Restore
    update_ticket("T001", {"status": orig_status})
