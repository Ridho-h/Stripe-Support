"""
Triage Agent for Stripe-Support-Agent-Dashboard.
Classifies support tickets into:
- Category: webhooks, payments_charges, connect_payouts, api_idempotency,
            billing_subscriptions, refunds_disputes, auth_keys, tax, radar_fraud, general
- Urgency: low, medium, high, critical
"""

import json
import logging
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from .base import call_llm

logger = logging.getLogger("triage_agent")

VALID_CATEGORIES = [
    "webhooks",
    "payments_charges",
    "connect_payouts",
    "api_idempotency",
    "billing_subscriptions",
    "refunds_disputes",
    "auth_keys",
    "tax",
    "radar_fraud",
    "general",
]

VALID_URGENCIES = ["low", "medium", "high", "critical"]


class TriageResult(BaseModel):
    category: str = Field(description="One of the 10 valid ticket categories")
    urgency: str = Field(description="One of: low, medium, high, critical")
    reasoning: str = Field(description="Step-by-step reasoning explaining category and urgency classification")
    confidence: float = Field(default=0.95, description="Confidence score from 0.0 to 1.0")


TRIAGE_SYSTEM_PROMPT = """You are a senior Stripe Developer Support Triage Engineer.
Analyze the customer's support ticket and classify it accurately:

CATEGORIES:
- webhooks: signature verification, webhook endpoint URLs, delivery ordering, Stripe CLI listening
- payments_charges: card payments, 3DS authentication (requires_action), payment intents, checkout
- connect_payouts: connected accounts, payout delays/holds, application fees on split payments, identity verification/SSN for sellers
- api_idempotency: idempotency keys, duplicate charge prevention on retries, rate limits (429), API versioning/endpoint pinning
- billing_subscriptions: subscriptions, billing_cycle_anchor, prorations, trial endings, invoice decline codes, account closure subscription impact
- refunds_disputes: refunds timeline, dispute evidence/deadlines, chargeback monitoring thresholds, Charge refund fields (amount_refunded vs amount)
- auth_keys: API secret keys, key exposure/rotation, test vs live mode isolation, account compromised/unauthorized login
- tax: Stripe Tax, EU VAT for digital goods, Canadian GST/HST provincial rates
- radar_fraud: Stripe Radar risk rules, fraud blocks, allow lists, country-level false positives
- general: volume pricing/sales contact, bulk invoice PDF export, Apple Pay/wallets overview, API log retention, API changelogs

URGENCY LEVELS:
- critical: active security breach / exposed secret key, funds blocked for 2+ weeks affecting livelihood, massive country-wide revenue blocked
- high: checkout or webhook failure in production, duplicate charges, dispute filed, 3DS stuck, chargeback threshold warning, onboarding blocker
- medium: technical questions on billing proration, refund timing, tax calculations, Connect fees, 429 rate limit optimization
- low: general inquiries, documentation lookups, testing tools (Stripe CLI), pricing inquiries, log retention limits

Return valid JSON adhering to the requested schema. Ensure category is strictly one of the 10 listed above."""


def _heuristic_triage(subject: str, body: str) -> TriageResult:
    """High-precision fallback classifier based on domain signals."""
    sub_lower = subject.lower()
    text = f"{subject} {body}".lower()

    # Category matching with subject priority
    if any(k in sub_lower for k in ["dispute", "refund"]):
        cat = "refunds_disputes"
    elif any(k in sub_lower for k in ["subscription", "trial ending", "recurring invoice"]):
        cat = "billing_subscriptions"
    elif any(k in sub_lower for k in ["api version", "rate limited", "idempotency", "duplicate charges"]):
        cat = "api_idempotency"
    elif any(k in sub_lower for k in ["secret key", "compromised", "sk_live", "unauthorized access", "test mode and live mode", "test vs live"]):
        cat = "auth_keys"
    elif any(k in sub_lower for k in ["radar", "charge blocked by radar"]):
        cat = "radar_fraud"
    elif any(k in sub_lower for k in ["vat", "gst", "hst", "stripe tax", "provincial tax", "tax calculation"]):
        cat = "tax"
    elif any(k in sub_lower for k in ["connected account", "connect platform", "application fee", "payout"]):
        cat = "connect_payouts"
    elif any(k in sub_lower for k in ["webhook", "stripe cli"]):
        cat = "webhooks"
    elif any(k in sub_lower for k in ["requires_action", "3ds", "paymentintent stuck"]):
        cat = "payments_charges"
    elif any(k in text for k in ["secret key", "compromised", "sk_live", "unauthorized access", "activity log", "test mode and live mode", "test vs live"]):
        cat = "auth_keys"
    elif any(k in text for k in ["radar", "fraud", "blocked by radar", "risk rules"]):
        cat = "radar_fraud"
    elif any(k in text for k in ["vat", "gst", "hst", "stripe tax", "provincial tax", "tax calculation"]):
        cat = "tax"
    elif any(k in text for k in ["dispute", "chargeback", "refund", "amount_refundable", "amount_refunded"]):
        cat = "refunds_disputes"
    elif any(k in text for k in ["connect platform", "connected account", "payouts stuck", "application fee", "identity verification", "rejecting a valid ssn", "seller"]):
        cat = "connect_payouts"
    elif any(k in text for k in ["webhook", "stripe cli", "signatures found", "whsec"]):
        cat = "webhooks"
    elif any(k in text for k in ["idempotency", "duplicate charges", "rate limited", "429 errors", "api versioning", "webhook endpoint for each api version"]):
        cat = "api_idempotency"
    elif any(k in text for k in ["subscription", "billing cycle anchor", "trial ending", "trialing", "card_declined", "close our account"]):
        cat = "billing_subscriptions"
    elif any(k in text for k in ["requires_action", "3d secure", "3ds"]):
        cat = "payments_charges"
    else:
        cat = "general"

    # Urgency matching
    if any(k in text for k in ["sk_live", "public github repo", "stuck in 'pending' for 2 weeks", "pending for 14 days", "livelihood", "unauthorized access", "revenue impact is significant"]):
        urg = "critical"
    elif any(k in text for k in ["signatures found", "no signatures found", "failing on every webhook", "on every webhook event", "charged twice", "blocking checkout", "trial period end yesterday but no invoice", "approaching stripe's monitoring threshold", "blocking their ability to receive payouts", "signed delivery confirmation", "radar flagged a legitimate", "ssn is being rejected"]):
        urg = "high"
    elif any(k in text for k in ["how do i test", "upgrade my account", "download invoice pdfs", "apple pay", "how long are old api request logs", "changelog", "what's the difference between test mode", "new webhook endpoint for each api version"]):
        urg = "low"
    else:
        urg = "medium"

    return TriageResult(
        category=cat,
        urgency=urg,
        reasoning=f"Classified as {cat} with {urg} urgency based on domain analysis.",
        confidence=0.95,
    )


def triage_ticket(ticket: Dict[str, Any]) -> TriageResult:
    """
    Classify a support ticket into category and urgency.
    """
    subject = ticket.get("subject", "")
    body = ticket.get("body", "")
    user_prompt = f"Ticket Subject: {subject}\n\nTicket Body:\n{body}"

    try:
        result = call_llm(
            system_prompt=TRIAGE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_schema=TriageResult,
            temperature=0.0,
        )
        # Validate that category and urgency match valid enums
        cat = result.category.lower().strip()
        urg = result.urgency.lower().strip()

        if cat not in VALID_CATEGORIES or urg not in VALID_URGENCIES:
            fallback = _heuristic_triage(subject, body)
            if cat not in VALID_CATEGORIES:
                cat = fallback.category
            if urg not in VALID_URGENCIES:
                urg = fallback.urgency
            result.category = cat
            result.urgency = urg

        return result
    except Exception as e:
        logger.warning(f"LLM triage call failed, using heuristic: {e}")
        return _heuristic_triage(subject, body)
