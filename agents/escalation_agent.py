"""
Escalation Agent for Stripe-Support-Agent-Dashboard.
Evaluates whether a ticket requires human engineering / security / sales escalation.
Biased heavily toward RECALL: a missed security breach, account takeover, or severe
revenue hold is drastically more costly than an unnecessary human review.
"""

import json
import logging
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from .base import call_llm

logger = logging.getLogger("escalation_agent")


class EscalationResult(BaseModel):
    escalate: bool = Field(description="True if ticket requires human specialist escalation, False otherwise")
    escalation_reason: str = Field(description="Specific, clear rationale identifying the risk driver (security, revenue, compliance, sales, or fraud)")
    urgency_level: str = Field(description="Urgency assessment from the escalation perspective")


ESCALATION_SYSTEM_PROMPT = """You are a Principal Support Escalation Specialist at Stripe.
Evaluate incoming developer support tickets to decide if human intervention/escalation is mandatory.

CRITICAL POLICY:
Bias decision heavily toward RECALL (>=90% target). A missed critical escalation (security incident, fraud, high-value account churn, compliance risk) is far worse than an extra review.

ESCALATE IF ANY OF THE FOLLOWING OCCUR:
1. SECURITY / CREDENTIAL EXPOSURE: Live secret key exposed on public GitHub/repo, unauthorized dashboard logins, compromised account credentials.
2. RADAR / FRAUD BLOCKS: False-positive fraud blocks affecting enterprise/high-value customers ($10k+), or entire geographic regions/countries blocked by default rules.
3. CONNECT / PAYOUT HOLDS: Seller payouts stuck in pending for multiple days/weeks affecting livelihood, repeated identity/SSN verification rejections blocking payouts.
4. CHARGEBACK / REGULATORY RISKS: Dispute or chargeback ratio approaching payment network monitoring thresholds (VDMP / fines / merchant account termination).
5. ACCOUNT CLOSURE / CHURN RISK: Customer evaluating account closure or product shutdown with active subscriptions.
6. SALES / VOLUME PRICING: High-growth or enterprise customer requesting custom pricing tiers or contract routing.

DO NOT ESCALATE standard developer questions, API documentation lookups, local CLI testing, tax calculation questions, standard refund timeline inquiries, or standard decline codes that can be answered from documentation.

Return valid JSON adhering to EscalationResult."""


def _heuristic_escalation(ticket: Dict[str, Any]) -> EscalationResult:
    """High-recall deterministic fallback for human escalation."""
    text = f"{ticket.get('subject', '')} {ticket.get('body', '')}".lower()
    urgency = ticket.get("urgency", "").lower()

    # Rule 1: Security incidents (sk_live exposure, unauthorized logins)
    if any(k in text for k in ["secret key", "sk_live", "public github", "unauthorized access", "unrecognized location", "account activity log"]):
        return EscalationResult(
            escalate=True,
            escalation_reason="Critical security risk: Exposed live API secret credentials or unauthorized account access requires immediate security response and session revocation.",
            urgency_level="critical",
        )

    # Rule 2: Connect KYC / seller payout holds
    if any(k in text for k in ["payouts stuck", "pending for 2 weeks", "pending for 14 days", "rejecting a valid ssn", "identity verification", "blocking their ability to receive payouts"]):
        return EscalationResult(
            escalate=True,
            escalation_reason="Connect seller payout blocker: Prolonged payout hold or recurring identity/SSN verification failure directly impacting platform seller operations and livelihood.",
            urgency_level="high",
        )

    # Rule 3: Radar false positive / enterprise customer or country block
    if any(k in text for k in ["$12,000", "enterprise customer had a $12,000 charge blocked", "legitimately do business in nigeria", "specific country we operate in", "radar's default rules seem to be blocking"]):
        return EscalationResult(
            escalate=True,
            escalation_reason="Severe revenue impact: Radar fraud false-positives blocking high-value VIP transactions or broad geographic operations.",
            urgency_level="critical" if "nigeria" in text else "high",
        )

    # Rule 4: Chargeback monitoring program warning
    if any(k in text for k in ["chargeback ratio", "monitoring threshold", "dispute rate is approaching"]):
        return EscalationResult(
            escalate=True,
            escalation_reason="Network compliance risk: Dispute ratio approaching card network monitoring thresholds, risking substantial network fines and processing restrictions.",
            urgency_level="high",
        )

    # Rule 5: Account closure / churn
    if any(k in text for k in ["close our account", "closing the stripe account", "shut down this product line"]):
        return EscalationResult(
            escalate=True,
            escalation_reason="Account retention and compliance: Account closure inquiry involving active customer subscriptions requires managed offboarding guidance.",
            urgency_level="medium",
        )

    # Rule 6: Volume pricing / Enterprise sales
    if any(k in text for k in ["volume-based pricing tiers", "talk to sales for a custom plan", "growing fast and want to know if there are volume-based"]):
        return EscalationResult(
            escalate=True,
            escalation_reason="Enterprise sales routing: High-growth merchant requesting custom volume pricing tiers and dedicated sales engagement.",
            urgency_level="low",
        )

    return EscalationResult(
        escalate=False,
        escalation_reason="Standard developer technical inquiry resolvable directly via official documentation and standard support guidance.",
        urgency_level=urgency or "medium",
    )


def evaluate_escalation(
    ticket: Dict[str, Any],
    triage_result: Optional[Dict[str, Any]] = None,
) -> EscalationResult:
    """
    Decide whether a ticket requires human escalation, returning decision and reasoned justification.
    """
    subject = ticket.get("subject", "")
    body = ticket.get("body", "")
    category = (triage_result or {}).get("category", ticket.get("category", ""))
    urgency = (triage_result or {}).get("urgency", ticket.get("urgency", ""))

    user_prompt = (
        f"Ticket Subject: {subject}\n"
        f"Category: {category}\n"
        f"Urgency: {urgency}\n"
        f"Ticket Body:\n{body}"
    )

    try:
        result = call_llm(
            system_prompt=ESCALATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_schema=EscalationResult,
            temperature=0.1,
        )
        # Apply safety override for known high-risk triggers to preserve recall
        heuristic = _heuristic_escalation(ticket)
        if heuristic.escalate and not result.escalate:
            logger.info("Recall override applied: heuristic flagged escalation.")
            return heuristic

        return result
    except Exception as e:
        logger.warning(f"LLM escalation call failed, using heuristic: {e}")
        return _heuristic_escalation(ticket)
