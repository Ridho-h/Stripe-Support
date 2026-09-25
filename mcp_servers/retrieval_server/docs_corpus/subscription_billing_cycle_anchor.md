---
topic: "subscription billing_cycle_anchor and proration behavior"
source_url: "https://docs.stripe.com/billing/subscriptions/billing-cycle"
category: "billing_subscriptions"
---
# Subscription Billing Cycle Anchors and Prorations

The billing_cycle_anchor parameter determines the point in time when recurring subscription periods reset and generate invoices. By default, a subscription's anchor matches the timestamp when it was created.

If you update an existing subscription to change its billing_cycle_anchor (for instance, aligning all customers to the 1st of the month using 'billing_cycle_anchor=now' or an upcoming timestamp), Stripe evaluates proration behavior via the 'proration_behavior' parameter. When set to 'create_prorations', Stripe computes line-item credits for unused time in the previous period and debits for the transitional period leading to the new anchor date. You can preview these calculations prior to confirmation using the Upcoming Invoice API.
