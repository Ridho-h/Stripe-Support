import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from agents.triage_agent import _heuristic_triage
from agents.escalation_agent import _heuristic_escalation
from evaluator import urgency_distance

def test_all():
    with open("labeled_tickets.json", encoding="utf-8") as f:
        tickets = json.load(f)["tickets"]

    cat_hits = 0
    urg_exact = 0
    urg_close = 0
    esc_hits = 0
    esc_tp = 0
    esc_fp = 0
    esc_fn = 0

    for t in tickets:
        # Triage
        triage_res = _heuristic_triage(t["subject"], t["body"])
        if triage_res.category == t["category"]:
            cat_hits += 1
        else:
            print(f"CAT MISS [{t['id']}]: GT={t['category']} != Pred={triage_res.category} | {t['subject']}")

        dist = urgency_distance(t["urgency"], triage_res.urgency)
        if dist == 0:
            urg_exact += 1
            urg_close += 1
        elif dist == 1:
            urg_close += 1
        else:
            print(f"SEVERE URG MISS [{t['id']}]: GT={t['urgency']} vs Pred={triage_res.urgency}")

        # Escalation
        esc_res = _heuristic_escalation(t)
        should_esc = t["escalate"]
        did_esc = esc_res.escalate
        if should_esc == did_esc:
            esc_hits += 1
        if should_esc and did_esc:
            esc_tp += 1
        elif should_esc and not did_esc:
            esc_fn += 1
            print(f"ESC MISS (FN) [{t['id']}]: should escalate! {t['subject']}")
        elif not should_esc and did_esc:
            esc_fp += 1
            print(f"ESC OVER (FP) [{t['id']}]: flagged unnecessarily: {t['subject']}")

    esc_positives = esc_tp + esc_fn
    esc_flagged = esc_tp + esc_fp

    esc_recall = (esc_tp / esc_positives) if esc_positives else 1.0
    esc_prec = (esc_tp / esc_flagged) if esc_flagged else 1.0

    print("--- RESULTS ---")
    print(f"Category Accuracy: {cat_hits}/30 ({cat_hits/30*100:.1f}%) [Threshold: >= 90%]")
    print(f"Urgency Exact: {urg_exact}/30 ({urg_exact/30*100:.1f}%) [Threshold: >= 75%]")
    print(f"Urgency Close (+-1): {urg_close}/30 ({urg_close/30*100:.1f}%) [Threshold: >= 95%]")
    print(f"Escalation Recall: {esc_tp}/{esc_positives} ({esc_recall*100:.1f}%) [Threshold: >= 90%]")
    print(f"Escalation Precision: {esc_tp}/{esc_flagged} ({esc_prec*100:.1f}%) [Threshold: >= 70%]")

if __name__ == "__main__":
    test_all()
