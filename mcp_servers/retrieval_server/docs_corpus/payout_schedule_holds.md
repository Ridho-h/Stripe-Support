---
topic: "payout schedule delays / account verification holds"
source_url: "https://docs.stripe.com/connect/payouts"
category: "connect_payouts"
---
# Connect Payout Delays and Account Verification Holds

On Stripe Connect platforms, funds collected from charges are transferred to connected accounts based on their configured payout schedule (e.g., daily rolling, weekly, or manual). When connected account payouts remain in 'pending' status for extended periods, it frequently signals an underlying compliance review or identity verification hold.

Even if an account initially appeared verified, Stripe periodically requests updated business documentation, identity proofs, or beneficial ownership details. If the account owner has unaddressed requirements in the 'requirements.currently_due' or 'requirements.past_due' fields of their Account object, payouts will be paused. Platform operators can inspect the Account API or Connect Dashboard to review active restrictions and assist the seller with remediation.
