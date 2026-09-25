"""
Ticket MCP Server.
Exposes tools for retrieving, listing, and updating customer support tickets.
Backed by SQLite seeded from labeled_tickets.json.
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    from mcp.server.mcpserver import MCPServer as FastMCP

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from .db import get_ticket as db_get_ticket
    from .db import list_tickets as db_list_tickets
    from .db import update_ticket as db_update_ticket
    from .db import init_db
except ImportError:
    from db import get_ticket as db_get_ticket
    from db import list_tickets as db_list_tickets
    from db import update_ticket as db_update_ticket
    from db import init_db

logger = logging.getLogger("ticket_server")
mcp = FastMCP("ticket-server")


@mcp.tool()
def get_ticket(id: str) -> Dict[str, Any]:
    """
    Retrieve a customer support ticket by its ID (e.g. 'T001').

    Args:
        id: Ticket identifier.

    Returns:
        dict: Ticket details including subject, body, category, urgency, escalate status, etc.
    """
    ticket = db_get_ticket(id)
    if ticket is None:
        return {"error": f"Ticket '{id}' not found."}
    return ticket


@mcp.tool()
def list_tickets(
    status: Optional[str] = None,
    category: Optional[str] = None,
    urgency: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List customer support tickets, optionally filtered by status, category, or urgency.

    Args:
        status: Optional filter by status ('open', 'triaged', 'drafted', 'escalated', 'closed').
        category: Optional filter by category (e.g. 'webhooks', 'payments_charges').
        urgency: Optional filter by urgency ('low', 'medium', 'high', 'critical').

    Returns:
        list of dicts: List of matching tickets.
    """
    # Normalize empty strings to None
    s = status if status and status.strip() else None
    c = category if category and category.strip() else None
    u = urgency if urgency and urgency.strip() else None
    return db_list_tickets(status=s, category=c, urgency=u)


@mcp.tool()
def update_ticket(id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update fields on a customer support ticket.

    Args:
        id: Ticket identifier (e.g. 'T001').
        fields: Dictionary of fields to update (e.g. {'status': 'triaged', 'draft_reply': '...'}).

    Returns:
        dict: The updated ticket object.
    """
    updated = db_update_ticket(id, fields)
    if updated is None:
        return {"error": f"Ticket '{id}' not found or could not be updated."}
    return updated


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ticket MCP Server")
    parser.add_argument("--test", action="store_true", help="Run quick self-test of tools")
    args = parser.parse_args()

    if args.test:
        print("[Ticket Server] Running self-tests...")
        init_db()
        t1 = get_ticket("T001")
        print(f"Retrieved T001: {t1.get('id')} - {t1.get('subject')}")
        all_t = list_tickets()
        print(f"Total tickets loaded: {len(all_t)}")
        assert len(all_t) >= 30, f"Expected at least 30 tickets, got {len(all_t)}"
        up = update_ticket("T001", {"status": "in_progress"})
        print(f"Updated status for T001: {up.get('status')}")
        assert up.get("status") == "in_progress"
        # Restore
        update_ticket("T001", {"status": "open"})
        print("[Ticket Server] Self-tests passed successfully.")
    else:
        mcp.run()
