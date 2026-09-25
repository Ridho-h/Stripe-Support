---
topic: "API versioning and webhook endpoint version pinning"
source_url: "https://docs.stripe.com/api/versioning"
category: "api_idempotency"
---
# API Versioning and Webhook Endpoint Version Pinning

Stripe pins API versions at both the account level and the webhook endpoint level. When you upgrade your account's default API version in the Dashboard or test with the 'Stripe-Version' header, existing webhook endpoints are NOT automatically modified or broken.

Each webhook endpoint is permanently pinned to the API version that was active when the endpoint was created. Upgrading your account API version will not change event schemas sent to that webhook endpoint. If you wish to migrate a webhook endpoint to a newer schema version, you can test the new version on a secondary endpoint or explicitly update the endpoint's pinned version in Dashboard > Webhooks after updating your ingestion code.
