---
topic: "API rate limits and bulk data migration strategies"
source_url: "https://docs.stripe.com/rate-limits"
category: "api_idempotency"
---
# API Rate Limits and Bulk Data Migration Strategies

Stripe enforces rate limits to maintain infrastructure stability and availability. Standard live mode limits are approximately 100 read requests per second and 100 write requests per second under normal operation. When limits are exceeded, the API responds with HTTP status code 429 Too Many Requests.

When performing large-scale customer migrations (such as importing tens of thousands of records):
1. Implement exponential backoff and jitter on all retry attempts when receiving 429 responses.
2. Throttle concurrency across workers so total outbound requests stay well within rate limits.
3. Contact Stripe Support prior to massive scheduled migrations to request temporary rate limit increases or coordinate secure bulk card data transfers through Stripe's PCI-certified migration service.
