---
topic: "API request log retention period"
source_url: "https://docs.stripe.com/dashboard#logs"
category: "general"
---
# Stripe API Request Log Retention Policy

Stripe retains detailed API request and response logs in the Stripe Dashboard for 30 calendar days. These logs capture HTTP headers, request payloads, response bodies, and latency metrics for debugging purposes.

Logs older than 30 days are automatically expunged from the interactive Dashboard and cannot be retrieved retroactively. For long-term audit compliance, debugging historical transactions, or internal data warehousing:
- Stream webhook event payloads to an internal database or log management platform (like Datadog, BigQuery, or CloudWatch).
- Maintain an internal event ledger recording key transaction IDs, request parameters, and status responses permanently.
