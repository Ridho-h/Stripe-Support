"""
Multi-Agent Orchestrator Pipeline for Stripe-Support-Agent-Dashboard.
Runs the 4 agents in sequence per ticket:
1. Triage Agent (Category & Urgency)
2. Retrieval Agent (Curated Stripe documentation search via MCP)
3. Drafting Agent (Grounded customer response)
4. Escalation Agent (High-recall human escalation review)

Logs structured JSON per stage consumed by evaluator.py and the Dashboard trace view.
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from agents.triage_agent import triage_ticket
from agents.retrieval_agent import retrieve_docs
from agents.drafting_agent import draft_reply
from agents.escalation_agent import evaluate_escalation
from mcp_servers.ticket_server.server import get_ticket, update_ticket

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("orchestrator_pipeline")


def run_ticket_pipeline(ticket: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the complete 4-stage pipeline for a single support ticket.
    Returns a dictionary containing:
      - ticket_id: ID of the ticket
      - stages: list of structured stage execution objects
      - prediction: evaluator.py formatted prediction dictionary
      - latency_ms: total execution latency
    """
    ticket_id = ticket.get("id", "UNKNOWN")
    start_time = time.time()
    stages = []

    # -------------------------------------------------------------
    # Stage 1: Triage Agent
    # -------------------------------------------------------------
    s1_start = time.time()
    triage_res = triage_ticket(ticket)
    s1_latency = round((time.time() - s1_start) * 1000, 1)

    stage_1 = {
        "agent": "Triage Agent",
        "stage_index": 1,
        "status": "completed",
        "output": {
            "category": triage_res.category,
            "urgency": triage_res.urgency,
        },
        "reasoning": triage_res.reasoning,
        "confidence": triage_res.confidence,
        "latency_ms": s1_latency,
        "timestamp": datetime.utcnow().isoformat(),
    }
    stages.append(stage_1)

    # -------------------------------------------------------------
    # Stage 2: Retrieval Agent
    # -------------------------------------------------------------
    s2_start = time.time()
    retrieval_res = retrieve_docs(ticket, top_k=3)
    s2_latency = round((time.time() - s2_start) * 1000, 1)

    stage_2 = {
        "agent": "Retrieval Agent",
        "stage_index": 2,
        "status": "completed",
        "output": {
            "retrieved_doc_topics": retrieval_res.retrieved_doc_topics,
            "passages": retrieval_res.passages,
        },
        "reasoning": retrieval_res.reasoning,
        "confidence": 1.0,
        "latency_ms": s2_latency,
        "timestamp": datetime.utcnow().isoformat(),
    }
    stages.append(stage_2)

    # -------------------------------------------------------------
    # Stage 3: Drafting Agent
    # -------------------------------------------------------------
    s3_start = time.time()
    draft_res = draft_reply(
        ticket=ticket,
        retrieval_result={
            "retrieved_doc_topics": retrieval_res.retrieved_doc_topics,
            "passages": retrieval_res.passages,
        },
    )
    s3_latency = round((time.time() - s3_start) * 1000, 1)

    stage_3 = {
        "agent": "Drafting Agent",
        "stage_index": 3,
        "status": "completed",
        "output": {
            "draft_reply": draft_res.draft_reply,
            "cited_topics": draft_res.cited_topics,
        },
        "reasoning": draft_res.reasoning,
        "confidence": 0.95,
        "latency_ms": s3_latency,
        "timestamp": datetime.utcnow().isoformat(),
    }
    stages.append(stage_3)

    # -------------------------------------------------------------
    # Stage 4: Escalation Agent
    # -------------------------------------------------------------
    s4_start = time.time()
    escalation_res = evaluate_escalation(
        ticket=ticket,
        triage_result={
            "category": triage_res.category,
            "urgency": triage_res.urgency,
        },
    )
    s4_latency = round((time.time() - s4_start) * 1000, 1)

    stage_4 = {
        "agent": "Escalation Agent",
        "stage_index": 4,
        "status": "completed",
        "output": {
            "escalate": escalation_res.escalate,
            "escalation_reason": escalation_res.escalation_reason,
            "urgency_level": escalation_res.urgency_level,
        },
        "reasoning": escalation_res.escalation_reason,
        "confidence": 0.95,
        "latency_ms": s4_latency,
        "timestamp": datetime.utcnow().isoformat(),
    }
    stages.append(stage_4)

    total_latency = round((time.time() - start_time) * 1000, 1)

    # evaluator.py prediction format
    prediction = {
        "category": triage_res.category,
        "urgency": triage_res.urgency,
        "retrieved_doc_topics": retrieval_res.retrieved_doc_topics,
        "escalate": escalation_res.escalate,
        "escalation_reason": escalation_res.escalation_reason,
        "draft_reply": draft_res.draft_reply,
    }

    # Update database record via ticket server
    update_ticket(
        id=ticket_id,
        fields={
            "status": "escalated" if escalation_res.escalate else "drafted",
            "predicted_category": triage_res.category,
            "predicted_urgency": triage_res.urgency,
            "retrieved_doc_topics": retrieval_res.retrieved_doc_topics,
            "escalate": escalation_res.escalate,
            "escalation_reason": escalation_res.escalation_reason,
            "draft_reply": draft_res.draft_reply,
        },
    )

    return {
        "ticket_id": ticket_id,
        "stages": stages,
        "prediction": prediction,
        "total_latency_ms": total_latency,
    }


def run_pipeline_all(
    tickets_path: str = "labeled_tickets.json",
    predictions_path: str = "predictions.json",
    traces_path: str = "pipeline_traces.json",
) -> Dict[str, Any]:
    """
    Run all tickets through the 4-agent pipeline and save predictions and traces.
    """
    logger.info(f"Loading dataset from {tickets_path}...")
    with open(tickets_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        tickets = data.get("tickets", [])

    logger.info(f"Running 4-agent pipeline over {len(tickets)} tickets...")
    predictions = {}
    traces = {}

    for i, t in enumerate(tickets, 1):
        tid = t["id"]
        logger.info(f"[{i}/{len(tickets)}] Processing {tid}: '{t['subject'][:40]}...'")
        result = run_ticket_pipeline(t)
        predictions[tid] = result["prediction"]
        traces[tid] = {
            "ticket_id": tid,
            "subject": t.get("subject", ""),
            "body": t.get("body", ""),
            "ground_truth": {
                "category": t.get("category"),
                "urgency": t.get("urgency"),
                "escalate": t.get("escalate"),
                "doc_topic": t.get("doc_topic"),
                "difficulty": t.get("difficulty"),
            },
            "stages": result["stages"],
            "prediction": result["prediction"],
            "total_latency_ms": result["total_latency_ms"],
        }

    logger.info(f"Saving predictions to {predictions_path}...")
    with open(predictions_path, "w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=2)

    logger.info(f"Saving structured traces to {traces_path}...")
    with open(traces_path, "w", encoding="utf-8") as f:
        json.dump(traces, f, indent=2)

    logger.info("Pipeline execution completed successfully.")
    return predictions


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Agent Pipeline Orchestrator")
    parser.add_argument("--all", action="store_true", help="Process all tickets in labeled_tickets.json")
    parser.add_argument("--ticket", type=str, help="Process a single ticket by ID (e.g. T001)")
    parser.add_argument("--eval", action="store_true", help="Run evaluator.py after pipeline completion")
    args = parser.parse_args()

    if args.ticket:
        t = get_ticket(args.ticket)
        if not t or "error" in t:
            print(f"Error: Ticket {args.ticket} not found.")
            sys.exit(1)
        res = run_ticket_pipeline(t)
        print(json.dumps(res, indent=2))
    elif args.all or args.eval:
        run_pipeline_all()
        if args.eval:
            from evaluator import evaluate
            eval_result = evaluate(
                tickets_path="labeled_tickets.json",
                predictions_path="predictions.json",
                draft_scores_path="draft_scores.json",
            )
            with open("metrics.json", "w", encoding="utf-8") as f:
                json.dump(eval_result, f, indent=2)
            print("\nEvaluation Results:")
            print(json.dumps(eval_result, indent=2))
    else:
        parser.print_help()
