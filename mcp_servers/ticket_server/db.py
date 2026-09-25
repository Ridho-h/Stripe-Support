"""
SQLite Database Layer for Ticket MCP Server.
Seeds from labeled_tickets.json and supports production CRUD operations.
"""

import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tickets.db")
DEFAULT_SEED_PATH = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "labeled_tickets.json")
)


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(
    db_path: str = DEFAULT_DB_PATH,
    seed_json_path: str = DEFAULT_SEED_PATH,
    force_reseed: bool = False,
) -> None:
    """Initialize SQLite database schema and seed from labeled_tickets.json if empty."""
    conn = get_connection(db_path)
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id TEXT PRIMARY KEY,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                category TEXT NOT NULL,
                urgency TEXT NOT NULL,
                escalate INTEGER NOT NULL,
                doc_topic TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                predicted_category TEXT,
                predicted_urgency TEXT,
                retrieved_doc_topics TEXT,
                escalation_reason TEXT,
                draft_reply TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor = conn.execute("SELECT COUNT(*) FROM tickets")
        count = cursor.fetchone()[0]

        if count == 0 or force_reseed:
            if force_reseed:
                conn.execute("DELETE FROM tickets")

            if os.path.exists(seed_json_path):
                with open(seed_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    tickets = data.get("tickets", [])
                    for t in tickets:
                        conn.execute(
                            """
                            INSERT OR REPLACE INTO tickets (
                                id, subject, body, category, urgency, escalate,
                                doc_topic, difficulty, status, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)
                            """,
                            (
                                t["id"],
                                t["subject"],
                                t["body"],
                                t["category"],
                                t["urgency"],
                                1 if t.get("escalate") else 0,
                                t.get("doc_topic", ""),
                                t.get("difficulty", "medium"),
                                datetime.utcnow().isoformat(),
                            ),
                        )
    conn.close()


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    d = dict(row)
    d["escalate"] = bool(d["escalate"])
    if d.get("retrieved_doc_topics"):
        try:
            d["retrieved_doc_topics"] = json.loads(d["retrieved_doc_topics"])
        except (json.JSONDecodeError, TypeError):
            if isinstance(d["retrieved_doc_topics"], str):
                d["retrieved_doc_topics"] = [
                    t.strip() for t in d["retrieved_doc_topics"].split(",") if t.strip()
                ]
    else:
        d["retrieved_doc_topics"] = []
    return d


def get_ticket(ticket_id: str, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve a single ticket by its unique ID."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id.strip(),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return _row_to_dict(row)
    return None


def list_tickets(
    status: Optional[str] = None,
    category: Optional[str] = None,
    urgency: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> List[Dict[str, Any]]:
    """List tickets with optional filtering by status, category, or urgency."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    query = "SELECT * FROM tickets WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status.strip())
    if category:
        query += " AND category = ?"
        params.append(category.strip())
    if urgency:
        query += " AND urgency = ?"
        params.append(urgency.strip())

    query += " ORDER BY id ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def update_ticket(
    ticket_id: str,
    fields: Dict[str, Any],
    db_path: str = DEFAULT_DB_PATH,
) -> Optional[Dict[str, Any]]:
    """Update fields of an existing ticket and return updated ticket dict."""
    init_db(db_path)
    conn = get_connection(db_path)
    allowed_fields = {
        "status",
        "predicted_category",
        "predicted_urgency",
        "retrieved_doc_topics",
        "escalation_reason",
        "draft_reply",
        "escalate",
    }

    updates = []
    values = []

    for k, v in fields.items():
        if k in allowed_fields:
            if k == "escalate":
                updates.append("escalate = ?")
                values.append(1 if v else 0)
            elif k == "retrieved_doc_topics" and isinstance(v, (list, tuple)):
                updates.append("retrieved_doc_topics = ?")
                values.append(json.dumps(v))
            else:
                updates.append(f"{k} = ?")
                values.append(v)

    if not updates:
        conn.close()
        return get_ticket(ticket_id, db_path)

    updates.append("updated_at = ?")
    values.append(datetime.utcnow().isoformat())
    values.append(ticket_id.strip())

    with conn:
        conn.execute(
            f"UPDATE tickets SET {', '.join(updates)} WHERE id = ?",
            values,
        )
    conn.close()
    return get_ticket(ticket_id, db_path)


def reset_db(db_path: str = DEFAULT_DB_PATH, seed_json_path: str = DEFAULT_SEED_PATH) -> None:
    """Reset and re-seed the SQLite database."""
    init_db(db_path, seed_json_path, force_reseed=True)
