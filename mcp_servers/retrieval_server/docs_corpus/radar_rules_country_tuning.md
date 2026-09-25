---
topic: "Radar risk rules by country and custom rule tuning"
source_url: "https://docs.stripe.com/radar/rules/country"
category: "radar_fraud"
---
# Radar Risk Rules by Geographic Region and Custom Tuning

Stripe Radar's default machine learning models evaluate geographic factors, including card issuing country, IP geolocation, and international dispute patterns. In specific regions with higher historical fraud baselines (such as certain emerging markets), default risk scoring can trigger elevated false-positive block rates for legitimate domestic or regional merchants.

To tune Radar rules for legitimate international operations:
1. Add custom allow or 3DS rules in Radar: 'Request 3D Secure if :ip_country: == "NG" and :risk_level: == "elevated"'. This shifts chargeback liability to the issuer while permitting genuine transactions.
2. Whitelist known corporate customers or verified payment methods.
3. Review blocked payments in the Dashboard to provide feedback to Radar ML models by marking false positives as safe.
