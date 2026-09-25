---
topic: "trial_end webhook events and invoice generation timing"
source_url: "https://docs.stripe.com/billing/subscriptions/trials"
category: "billing_subscriptions"
---
# Subscription Trial End Webhooks and Invoice Generation

When a subscription with a trial period reaches its trial_end timestamp, Stripe triggers a series of lifecycle events to transition the subscription from 'trialing' to 'active' and generate the initial recurring invoice.

Approximately three days before a trial expires, Stripe fires 'customer.subscription.trial_will_end' so merchants can notify customers. When the trial formally expires, Stripe fires 'customer.subscription.updated' and creates an invoice. The invoice typically remains in draft status for approximately one hour before being finalized and charged. If customers remain in 'trialing' status after trial expiration, check whether the trial_end timestamp was set in the future or if invoice auto-advance settings were disabled.
