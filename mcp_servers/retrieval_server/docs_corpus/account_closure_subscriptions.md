---
topic: "account closure and subscription/data handling implications"
source_url: "https://docs.stripe.com/account/close"
category: "billing_subscriptions"
---
# Account Closure Implications for Active Subscriptions and Data

Closing a Stripe account is an irreversible action that terminates payment processing capabilities. When an account is closed:
- All active recurring subscriptions are canceled and will not generate future invoices or automatic charges.
- Any pending payouts are settled according to standard payout schedules, provided no outstanding negative balances or compliance holds exist.
- Access to the Dashboard transitions to read-only historical reporting mode.

Before closing an account, merchants should explicitly export customer data, invoices, and accounting reports. If transitioning customers to another payment provider, merchants should request a secure card data migration prior to closure, as card details cannot be exported or migrated after an account is formally closed.
