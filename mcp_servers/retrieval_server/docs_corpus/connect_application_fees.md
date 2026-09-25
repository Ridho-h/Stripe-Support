---
topic: "application fees and fee responsibility in Connect"
source_url: "https://docs.stripe.com/connect/direct-charges"
category: "connect_payouts"
---
# Connect Application Fees and Processing Fee Allocation

In Stripe Connect integrations, the platform can collect an application fee on payments processed through connected accounts by specifying the 'application_fee_amount' parameter on charges or PaymentIntents.

Understanding how Stripe's own payment processing fees interact with application fees depends on the charge type:
- On Direct Charges: The connected account is the merchant of record and pays Stripe's processing fee by default. The platform receives the exact 'application_fee_amount' transferred to the platform balance.
- On Destination Charges: The platform is responsible for Stripe processing fees, refunds, and chargebacks. Stripe fees are deducted from the gross charge before remaining funds are transferred to the connected account, adjusted by the application fee.
