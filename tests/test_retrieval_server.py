"""
Unit tests for Retrieval MCP Server.
"""

import os
import pytest
from mcp_servers.retrieval_server.retriever import DocsRetriever, parse_frontmatter, _tokenize
from mcp_servers.retrieval_server.server import search_docs


def test_parse_frontmatter():
    sample = """---
topic: "test topic"
source_url: "https://docs.stripe.com/test"
category: "webhooks"
---
# Test Title
This is body paragraph 1.

This is body paragraph 2."""
    meta, body = parse_frontmatter(sample)
    assert meta["topic"] == "test topic"
    assert meta["source_url"] == "https://docs.stripe.com/test"
    assert meta["category"] == "webhooks"
    assert "This is body paragraph 1." in body


def test_tokenize():
    tokens = _tokenize("Hello, World! This is Stripe-CLI 2026.")
    assert "hello" in tokens
    assert "world" in tokens
    assert "stripe-cli" in tokens or "stripe" in tokens


def test_search_docs_returns_results():
    results = search_docs("webhook signature verification", top_k=3)
    assert len(results) == 3
    assert all("doc_topic" in r for r in results)
    assert all("snippet" in r for r in results)
    assert all("source" in r for r in results)
    assert all("score" in r for r in results)


def test_search_docs_top_k_respected():
    results_1 = search_docs("idempotency key", top_k=1)
    results_5 = search_docs("idempotency key", top_k=5)
    assert len(results_1) == 1
    assert len(results_5) == 5


def test_search_docs_empty_query():
    results = search_docs("", top_k=3)
    assert results == []


def test_search_docs_ordering():
    results = search_docs("3DS requires_action authentication", top_k=3)
    assert len(results) >= 2
    assert results[0]["score"] >= results[1]["score"]


def test_search_docs_topic_precision():
    results = search_docs("secret key committed to public repo GitHub", top_k=1)
    assert len(results) == 1
    assert "API key exposure" in results[0]["doc_topic"]
    assert "https://docs.stripe.com/keys" in results[0]["source"]


def test_search_docs_radar():
    results = search_docs("Radar blocked $12,000 charge custom rules allow list", top_k=1)
    assert len(results) == 1
    assert "Radar" in results[0]["doc_topic"]
