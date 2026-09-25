---
topic: "refund processing timelines by payment method"
source_url: "https://docs.stripe.com/refunds"
category: "refunds_disputes"
---
# Refund Settlement Timelines by Payment Method

When a refund is submitted via the Stripe API or Dashboard and marked as 'succeeded', Stripe immediately submits the refund request to the card networks or underlying payment rail. However, the customer's financial institution requires processing time to post the credit to the account.

For credit and debit cards, refunds typically take between 5 to 10 business days to appear on the customer's statement, depending on the issuing bank's settlement cycle. In rare instances where charges are refunded on the same calendar day, the issuing bank may delete the original authorization entirely rather than posting a distinct credit line item (a reversal). For bank debit methods (ACH, SEPA), refunds may take additional business days to clear.
