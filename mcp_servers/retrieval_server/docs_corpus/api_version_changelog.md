---
topic: "API version changelog / upgrade guide"
source_url: "https://docs.stripe.com/upgrades"
category: "general"
---
# Stripe API Version Changelog and Upgrade Guides

Stripe publishes a comprehensive API Changelog documenting all backward-incompatible breaking changes, deprecations, and schema enhancements between releases.

Before upgrading your account's default API version:
1. Review the API Changelog for every release between your current version and the target version.
2. Note changes to response properties, renamed parameters, and altered webhook payloads.
3. Test your integration incrementally using the 'Stripe-Version' request header in your staging environment to execute requests against the new API version without altering production default behavior.
4. Upgrade your default account version in the Stripe Dashboard only after testing confirms full compatibility.
