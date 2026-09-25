---
topic: "Stripe CLI webhook forwarding"
source_url: "https://docs.stripe.com/stripe-cli/webhooks"
category: "webhooks"
---
# Local Webhook Testing with Stripe CLI

The Stripe CLI enables local testing by establishing a secure WebSocket connection to Stripe and forwarding live or test webhook events directly to your local development server without requiring public tunnels like ngrok.

To begin forwarding events, run 'stripe listen --forward-to localhost:4242/webhook'. The CLI will output a local webhook signing secret in the format whsec_test_.... You must update your local environment variables with this temporary CLI secret so signature verification succeeds locally. You can also trigger synthetic events on demand using commands such as 'stripe trigger payment_intent.succeeded' to validate handler logic during development.
