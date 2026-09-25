---
topic: "webhook delivery ordering guarantees (or lack thereof)"
source_url: "https://docs.stripe.com/webhooks"
category: "webhooks"
---
# Webhook Delivery Ordering and Concurrency Guarantees

Stripe does not guarantee that webhook events will be delivered in the exact chronological order in which they were generated. Because webhook deliveries are distributed across concurrent asynchronous workers and subject to network retries, an event like 'invoice.paid' can occasionally reach your server before 'invoice.created'.

Your webhook ingestion architecture must be designed defensively:
1. Do not assume strict event sequencing in internal state machines.
2. Use the 'created' timestamp on the enclosed Stripe object or query the Stripe API directly to fetch the authoritative, latest object state upon event receipt.
3. Make all event handlers idempotent by storing processed event IDs (evt_...) to prevent duplicate processing on retries.
