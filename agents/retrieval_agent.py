"""
Retrieval Agent for Stripe-Support-Agent-Dashboard.
Interfaces with the Retrieval MCP tool (search_docs) to find top relevant
documentation passages from the curated Stripe docs corpus.
"""

import logging
from typing import Any, Dict, List
from pydantic import BaseModel, Field

from mcp_servers.retrieval_server.server import search_docs

logger = logging.getLogger("retrieval_agent")


class RetrievalResult(BaseModel):
    retrieved_doc_topics: List[str] = Field(description="List of top doc topic strings")
    passages: List[Dict[str, Any]] = Field(description="Detailed passage objects containing topic, snippet, source, score")
    reasoning: str = Field(description="Reasoning on why these documentation passages were selected")


def retrieve_docs(ticket: Dict[str, Any], top_k: int = 3) -> RetrievalResult:
    """
    Search curated documentation using ticket subject and body.
    """
    subject = ticket.get("subject", "")
    body = ticket.get("body", "")
    query = f"{subject} {body}".strip()

    passages = search_docs(query=query, top_k=top_k)
    topics = [p["doc_topic"] for p in passages]

    reasoning = (
        f"Retrieved {len(passages)} documentation topic(s) matching ticket keywords: "
        f"{', '.join(topics[:3])}."
    )

    return RetrievalResult(
        retrieved_doc_topics=topics,
        passages=passages,
        reasoning=reasoning,
    )
