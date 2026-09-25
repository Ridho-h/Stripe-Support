import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcp_servers.retrieval_server.retriever import search_docs

def main():
    with open('labeled_tickets.json', encoding='utf-8') as f:
        tickets = json.load(f)['tickets']

    hits = 0
    misses = []
    for t in tickets:
        query = f"{t['subject']} {t['body']}"
        res = search_docs(query, top_k=3)
        retrieved_topics = [r['doc_topic'] for r in res]
        first_word = t['doc_topic'].split()[0].lower()
        hit = any(first_word in rt.lower() for rt in retrieved_topics)
        if hit:
            hits += 1
        else:
            misses.append((t['id'], t['doc_topic'], retrieved_topics))

    print(f"Retrieval Recall@3: {hits}/{len(tickets)} ({hits/len(tickets)*100:.1f}%)")
    for tid, target, got in misses:
        print(f"MISS [{tid}]: target '{target}' -> retrieved: {got}")

if __name__ == "__main__":
    main()
