---
topic: "account security incident response / 2FA enforcement"
source_url: "https://docs.stripe.com/security"
category: "auth_keys"
---
# Account Security Incident Response and 2FA Enforcement

Suspected unauthorized access to a Stripe account constitutes a critical security incident. If an unrecognized login or suspicious IP address is identified in the account activity log, take immediate protective action:
1. Change account passwords immediately and invalidate all active user sessions across all team members.
2. Enforce Two-Factor Authentication (2FA / MFA) across the entire Stripe account team in Dashboard settings.
3. Review team member roles and revoke permissions from any unfamiliar email addresses.
4. Inspect API keys, restricted keys, and webhook endpoints to verify no unauthorized credentials or endpoints were added.
5. Review recent bank account modifications and payout destinations to prevent funds redirection.
6. Report the incident immediately to Stripe Support and security operations.
