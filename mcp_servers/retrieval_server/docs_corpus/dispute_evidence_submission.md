---
topic: "dispute evidence submission and deadlines"
source_url: "https://docs.stripe.com/disputes/measuring-risk/responding"
category: "refunds_disputes"
---
# Dispute Evidence Submission Process and Deadlines

When a cardholder disputes a charge with their issuing bank, Stripe creates a Dispute object and immediately deducts the disputed amount plus a network dispute fee from the merchant's account balance.

Merchants have a strict deadline (typically 7 to 21 days, indicated by the 'evidence_details.due_by' timestamp) to submit counter-evidence. For fraudulent claims where delivery took place, effective evidence includes signed proof of delivery, tracking numbers from recognized carriers, matching billing and shipping addresses, IP access logs, and customer communication records. Evidence must be submitted before the deadline via the Dashboard or the Dispute Update API; once the deadline passes, submissions are rejected by card networks.
