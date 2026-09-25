---
topic: "decline codes and reading detailed failure reasons on invoices"
source_url: "https://docs.stripe.com/declines/codes"
category: "billing_subscriptions"
---
# Card Decline Codes and Investigating Recurring Invoice Failures

When an automatic recurring subscription invoice fails with a generic 'card_declined' error, the customer's issuing bank has refused the charge. While the high-level error may state 'card_declined', Stripe receives specific decline codes from the card network.

To find the exact decline reason:
1. Inspect the Invoice object and locate the associated PaymentIntent ('invoice.payment_intent').
2. In the PaymentIntent, look at the latest charge or 'last_payment_error.decline_code'.
3. Common decline codes include 'insufficient_funds', 'do_not_honor', 'expired_card', 'transaction_not_allowed', or 'suspected_fraud'.
4. For codes like 'do_not_honor' or 'generic_decline', banks refuse the transaction due to automated security rules on recurring charges; the cardholder must contact their issuing bank directly to authorize Stripe charges.
