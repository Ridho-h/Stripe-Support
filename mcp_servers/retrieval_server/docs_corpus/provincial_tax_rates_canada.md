---
topic: "provincial tax rates and address validation for Stripe Tax"
source_url: "https://docs.stripe.com/tax/canada"
category: "tax"
---
# Canadian Provincial Tax Rates (GST/HST/PST) and Address Validation

In Canada, indirect tax calculation depends heavily on the specific province or territory of the customer:
- Participating provinces (like Ontario, Nova Scotia, New Brunswick) impose a combined Harmonized Sales Tax (HST) (e.g. 13% in Ontario).
- Other provinces impose separate federal Goods and Services Tax (GST, 5%) plus Provincial Sales Tax (PST) or Quebec Sales Tax (QST).

If Stripe Tax calculated 5% GST instead of 13% HST for an Ontario customer, verify two factors:
1. Ensure your account has registered active tax obligations in Ontario under Stripe Tax settings. If registration is only enabled at the federal Canadian level, Stripe Tax collects solely federal GST.
2. Ensure the customer's shipping/billing postal code is validated as an Ontario address; incomplete postal codes default to federal rates.
