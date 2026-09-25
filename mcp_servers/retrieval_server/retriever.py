"""
Documentation Corpus Retriever for Stripe-Support-Agent-Dashboard.
Parses markdown files with YAML frontmatter from docs_corpus/ and indexes them
using BM25/TF-IDF scoring with topic boosting and keyword expansion.
"""

import math
import os
import re
from typing import Any, Dict, List, Optional

CORPUS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs_corpus")


def _tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric words."""
    return re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", text.lower())


def parse_frontmatter(content: str) -> tuple[Dict[str, str], str]:
    """Extract YAML frontmatter and body from markdown content."""
    meta = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            raw_meta = parts[1].strip()
            body = parts[2].strip()
            for line in raw_meta.splitlines():
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip()
                    val = val.strip().strip("\"'")
                    meta[key] = val
    return meta, body


class DocsRetriever:
    def __init__(self, corpus_dir: str = CORPUS_DIR):
        self.corpus_dir = corpus_dir
        self.documents: List[Dict[str, Any]] = []
        self._load_corpus()

    def _load_corpus(self):
        self.documents = []
        if not os.path.exists(self.corpus_dir):
            return

        for fname in os.listdir(self.corpus_dir):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(self.corpus_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                raw_text = f.read()

            meta, body = parse_frontmatter(raw_text)
            topic = meta.get("topic") or os.path.splitext(fname)[0].replace("_", " ")
            source_url = meta.get("source_url", "https://docs.stripe.com")
            category = meta.get("category", "general")

            # Extract first substantive paragraph for concise snippet
            paragraphs = [p.strip() for p in body.split("\n\n") if p.strip() and not p.startswith("#")]
            snippet = paragraphs[0] if paragraphs else body[:300]

            self.documents.append({
                "id": fname,
                "doc_topic": topic,
                "category": category,
                "source": source_url,
                "snippet": snippet,
                "body": body,
                "tokens": _tokenize(body),
                "topic_tokens": _tokenize(topic) + _tokenize(category),
            })

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search corpus using BM25-inspired term frequency with heavy weight on topic matches.
        """
        if not self.documents:
            self._load_corpus()
        if not self.documents:
            return []

        query_tokens = _tokenize(query)
        if not query_tokens:
            return [
                {
                    "doc_topic": d["doc_topic"],
                    "snippet": d["snippet"],
                    "source": d["source"],
                    "score": 0.0,
                }
                for d in self.documents[:top_k]
            ]

        # Calculate IDF-like weights
        total_docs = len(self.documents)
        doc_freq = {}
        for q in query_tokens:
            freq = sum(1 for d in self.documents if q in d["tokens"] or q in d["topic_tokens"])
            doc_freq[q] = freq

        scored = []
        for doc in self.documents:
            score = 0.0
            doc_tokens_set = set(doc["tokens"])
            topic_tokens_set = set(doc["topic_tokens"])

            for q in query_tokens:
                # IDF factor
                df = doc_freq.get(q, 0)
                idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1.0) if df > 0 else 0.1

                # Topic match bonus (4x multiplier)
                if q in topic_tokens_set:
                    score += 4.0 * idf

                # Body term frequency
                tf = doc["tokens"].count(q)
                if tf > 0:
                    score += (tf / (tf + 1.5)) * idf

            # Full phrase match bonus in topic
            if query.lower() in doc["doc_topic"].lower():
                score += 10.0

            scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, doc in scored[:top_k]:
            results.append({
                "doc_topic": doc["doc_topic"],
                "snippet": doc["snippet"],
                "source": doc["source"],
                "score": round(score, 3),
            })
        return results


_default_retriever = None


def get_retriever(corpus_dir: str = CORPUS_DIR) -> DocsRetriever:
    global _default_retriever
    if _default_retriever is None or _default_retriever.corpus_dir != corpus_dir:
        _default_retriever = DocsRetriever(corpus_dir)
    return _default_retriever


def search_docs(query: str, top_k: int = 3, corpus_dir: str = CORPUS_DIR) -> List[Dict[str, Any]]:
    retriever = get_retriever(corpus_dir)
    return retriever.search(query, top_k=top_k)
