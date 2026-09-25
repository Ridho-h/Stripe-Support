"""
Unit tests for Retrieval Agent.
"""

import pytest
from agents.retrieval_agent import RetrievalResult, retrieve_docs


def test_retrieve_docs_structure():
    ticket = {
        "id": "T001",
        "subject": "Webhook signature verification keeps failing",
        "body": "Using the raw request body before parsing JSON, and the signing secret matches.",
    }
    res = retrieve_docs(ticket, top_k=3)
    assert isinstance(res, RetrievalResult)
    assert len(res.retrieved_doc_topics) == 3
    assert len(res.passages) == 3
    assert "webhook" in res.retrieved_doc_topics[0].lower()
    assert len(res.reasoning) > 0


def test_retrieve_docs_topic_alignment():
    ticket = {
        "id": "T002",
        "subject": "Duplicate charges appearing for the same order",
        "body": "A customer was charged twice. Didn't pass an idempotency key.",
    }
    res = retrieve_docs(ticket, top_k=3)
    assert any("idempotency" in t.lower() for t in res.retrieved_doc_topics)
