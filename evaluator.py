"""
Evaluator for Stripe-Support-Agent-Dashboard.

Scores agent pipeline predictions against labeled_tickets.json using the
metrics defined in eval_rubric.md. Mirrors the evaluator pattern used in
Multi-Agent-Coding-Assistant (tasks/evaluator.py) and Multimodal-Food-Agent's
eval harness: run once, get a per-category table + composite score, saved
to metrics.json.

Expected `predictions` input shape (one dict per ticket id), produced by
running your orchestrator pipeline over labeled_tickets.json:

    {
      "T001": {
        "category": "webhooks",
        "urgency": "high",
        "retrieved_doc_topics": ["webhook signing secret rotation", ...],
        "escalate": false,
        "escalation_reason": "...",
        "draft_reply": "...",
      },
      ...
    }

Draft quality scores (factual/tone/actionability, 0-2 each) are supplied
separately as a manual or LLM-judge review file — see `draft_scores` below —
since that axis isn't auto-scorable from ground truth alone.
"""

import json
from collections import defaultdict

URGENCY_LEVELS = ["low", "medium", "high", "critical"]


def urgency_distance(a: str, b: str) -> int:
    return abs(URGENCY_LEVELS.index(a) - URGENCY_LEVELS.index(b))


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate(tickets_path: str, predictions_path: str, draft_scores_path: str | None = None):
    tickets = {t["id"]: t for t in load_json(tickets_path)["tickets"]}
    predictions = load_json(predictions_path)
    draft_scores = load_json(draft_scores_path) if draft_scores_path else {}

    per_category = defaultdict(list)
    severe_urgency_misses = []
    hallucinated_citations = []

    for tid, gt in tickets.items():
        pred = predictions.get(tid)
        if pred is None:
            continue

        category_hit = pred.get("category") == gt["category"]

        urg_dist = urgency_distance(gt["urgency"], pred.get("urgency", gt["urgency"]))
        urgency_exact = urg_dist == 0
        urgency_close = urg_dist <= 1
        if urg_dist >= 2:
            severe_urgency_misses.append(tid)

        retrieved = pred.get("retrieved_doc_topics", [])
        # naive keyword-overlap check; swap for embedding similarity if available
        citation_recall_at_3 = any(
            gt["doc_topic"].split()[0].lower() in r.lower() for r in retrieved[:3]
        )
        draft_cites = pred.get("draft_reply", "")
        cited_something_not_retrieved = (
            bool(draft_cites) and retrieved and not any(r.lower() in draft_cites.lower() for r in retrieved)
        )
        if cited_something_not_retrieved:
            hallucinated_citations.append(tid)

        should_escalate = gt["escalate"]
        did_escalate = pred.get("escalate", False)
        escalation_correct = should_escalate == did_escalate
        escalation_tp = should_escalate and did_escalate
        escalation_fn = should_escalate and not did_escalate
        escalation_fp = (not should_escalate) and did_escalate

        draft_quality = None
        if tid in draft_scores:
            s = draft_scores[tid]
            draft_quality = (s["factual"] + s["tone"] + s["actionability"]) / 6.0  # normalize to 0-1

        per_category[gt["category"]].append({
            "id": tid,
            "difficulty": gt["difficulty"],
            "category_hit": category_hit,
            "urgency_exact": urgency_exact,
            "urgency_close": urgency_close,
            "citation_recall_at_3": citation_recall_at_3,
            "escalation_correct": escalation_correct,
            "escalation_tp": escalation_tp,
            "escalation_fn": escalation_fn,
            "escalation_fp": escalation_fp,
            "draft_quality": draft_quality,
        })

    report = {"by_category": {}, "overall": {}}
    all_rows = [row for rows in per_category.values() for row in rows]

    def summarize(rows):
        n = len(rows)
        if n == 0:
            return {}
        escalate_positives = sum(r["escalation_tp"] + r["escalation_fn"] for r in rows)
        escalate_flagged = sum(r["escalation_tp"] + r["escalation_fp"] for r in rows)
        draft_scores_present = [r["draft_quality"] for r in rows if r["draft_quality"] is not None]
        return {
            "n": n,
            "triage_category_acc": round(sum(r["category_hit"] for r in rows) / n, 3),
            "triage_urgency_exact_acc": round(sum(r["urgency_exact"] for r in rows) / n, 3),
            "triage_urgency_close_acc": round(sum(r["urgency_close"] for r in rows) / n, 3),
            "citation_recall_at_3": round(sum(r["citation_recall_at_3"] for r in rows) / n, 3),
            "escalation_recall": round(
                sum(r["escalation_tp"] for r in rows) / escalate_positives, 3
            ) if escalate_positives else None,
            "escalation_precision": round(
                sum(r["escalation_tp"] for r in rows) / escalate_flagged, 3
            ) if escalate_flagged else None,
            "draft_quality_avg": round(sum(draft_scores_present) / len(draft_scores_present), 3)
            if draft_scores_present else None,
        }

    for cat, rows in per_category.items():
        report["by_category"][cat] = summarize(rows)
    report["overall"] = summarize(all_rows)
    report["flags"] = {
        "severe_urgency_misses": severe_urgency_misses,
        "hallucinated_citations": hallucinated_citations,
    }

    overall = report["overall"]
    composite_parts = [
        overall.get("triage_category_acc") or 0,
        overall.get("citation_recall_at_3") or 0,
        overall.get("escalation_recall") or 0,
        overall.get("draft_quality_avg") or 0,
    ]
    report["composite_score"] = round(sum(composite_parts) / 4, 3)

    return report


if __name__ == "__main__":
    result = evaluate(
        tickets_path="labeled_tickets.json",
        predictions_path="predictions.json",
        draft_scores_path="draft_scores.json",  # optional; omit arg if not yet scored
    )
    with open("metrics.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))
