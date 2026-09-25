---
topic: "Charge object refund fields (amount_refunded vs amount)"
source_url: "https://docs.stripe.com/api/charges/object"
category: "refunds_disputes"
---
# Charge Object Refund Fields: amount_refunded vs amount

When inspecting a Charge object following a partial or full refund, developers must distinguish between different financial attributes:
- 'amount': Represents the original total gross amount charged in the smallest currency unit (e.g., 10000 for $100.00). This field remains constant throughout the charge lifecycle.
- 'amount_refunded': Tracks the cumulative total amount that has been refunded to date. After a $20.00 refund on a $100.00 charge, 'amount' remains 10000 while 'amount_refunded' updates to 2000.
- 'refunded': A boolean flag that only flips to 'true' once the entire charge has been refunded ('amount_refunded == amount').

To compute remaining refundable funds, subtract 'amount_refunded' from 'amount'.
