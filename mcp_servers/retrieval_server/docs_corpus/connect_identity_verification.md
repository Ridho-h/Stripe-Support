---
topic: "identity verification failures in Connect onboarding"
source_url: "https://docs.stripe.com/connect/identity-verification"
category: "connect_payouts"
---
# Identity Verification and SSN Rejection in Connect Onboarding

During Stripe Connect onboarding, sellers must complete identity verification (Know Your Customer / KYC). When a Social Security Number (SSN) or national ID is repeatedly rejected:
1. Verification discrepancies typically stem from minor mismatches between the provided legal name, date of birth, and home address against credit bureau and government records.
2. Recent legal name changes, moves, or typos in the legal name field will cause automated matching algorithms to reject the input.
3. If automated verification fails repeatedly, Stripe allows users to upload government photo identification (driver's license or passport) and proof of address. Platform admins can inspect the Account API 'requirements.disabled_reason' field and share a generated verification update link with the seller.
