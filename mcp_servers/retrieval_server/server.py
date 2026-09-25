"""
Retrieval MCP Server.
Exposes search_docs tool over MCP protocol and direct function calling.
Searches curated Stripe documentation summaries from docs_corpus/.
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    from mcp.server.mcpserver import MCPServer as FastMCP

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from .retriever import search_docs as internal_search_docs
except ImportError:
    from retriever import search_docs as internal_search_docs

logger = logging.getLogger("retrieval_server")
mcp = FastMCP("retrieval-server")


@mcp.tool()
def search_docs(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Search the curated Stripe documentation corpus for relevant topics and guidance.

    Args:
        query: Search query or ticket description (e.g. 'webhook signature verification failed').
        top_k: Number of relevant doc passages to return (default: 3).

    Returns:
        list of dicts: [
            {
                "doc_topic": str,  # Topic title
                "snippet": str,    # Relevant excerpt / instructions
                "source": str      # Stripe official docs URL
            }
        ]
    """
    if not query or not query.strip():
        return []
    results = internal_search_docs(query=query.strip(), top_k=top_k)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrieval MCP Server")
    parser.add_argument("--test", action="store_true", help="Run quick self-test of retrieval tool")
    parser.add_argument("--query", type=str, default="webhook signature verification failing", help="Query to test")
    args = parser.parse_args()

    if args.test or args.query:
        print(f"[Retrieval Server] Testing search_docs for: '{args.query}'")
        res = search_docs(args.query, top_k=3)
        print(f"Found {len(res)} results:")
        print(json.dumps(res, indent=2))
        print("[Retrieval Server] Test completed.")
    else:
        mcp.run()
