---
topic: "webhook signing secret rotation / raw body middleware ordering"
source_url: "https://docs.stripe.com/webhooks/signatures"
category: "webhooks"
---
# Webhook Signature Verification and Raw Body Middleware

Stripe signs webhook events to verify that requests originate from Stripe and have not been tampered with. To verify signatures, your endpoint must use the raw, unparsed HTTP request body buffer. If JSON parsing middleware (like express.json() or bodyParser.json()) runs before Stripe's signature check, the payload is altered by deserialization, causing signature verification to fail with 'No signatures found matching the expected signature for payload'.

Ensure that the raw body is passed directly to stripe.webhooks.constructEvent(payload, sig, endpointSecret). Additionally, verify that the endpoint secret configured in your application matches the specific endpoint in the Stripe Dashboard (whsec_...). When rotating secrets, configure your application to temporarily accept signatures from both the old and new secrets until all deliveries settle.
