---
topic: "Stripe Tax automatic calculation for digital goods"
source_url: "https://docs.stripe.com/tax"
category: "tax"
---
# Automatic Tax Calculation for Digital Goods with Stripe Tax

Stripe Tax automates sales tax, VAT, and GST calculation, collection, and reporting for global transactions, including cross-border digital goods and SaaS subscriptions. To enable automatic tax calculation, merchants register their active tax obligations in the Stripe Dashboard and set the product's tax_code (e.g., txcd_10000000 for digital software).

When creating Invoices, Subscriptions, or Checkout sessions with 'automatic_tax: {enabled: true}', Stripe Tax calculates the applicable EU VAT or regional tax rate using the customer's billing and IP location evidence. For B2B transactions in the EU, if the customer provides a validated VAT identification number, Stripe Tax automatically applies the reverse charge mechanism (0% VAT).
