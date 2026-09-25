---
topic: "Radar custom rules and allow lists"
source_url: "https://docs.stripe.com/radar/rules"
category: "radar_fraud"
---
# Radar Custom Rules, Risk Evaluation, and Allow Lists

Stripe Radar uses machine learning models trained across the global Stripe network to assign each payment a risk score and risk level (normal, elevated, or highest). By default, Radar blocks payments classified as highest risk.

For legitimate high-value customers who encounter false-positive blocks, merchants can create Radar Allow Lists and custom rules. You can add a customer's email, card fingerprint, or IP address to an allow list. Allow rules (e.g. 'Allow if :email: in @trusted_customers') take precedence over default block rules. However, allow rules do not bypass issuer-level declines or 3D Secure liability shifts. High-value transactions can also be configured to require manual review rather than outright blocking.
