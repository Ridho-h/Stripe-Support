---
topic: "Payment Request Button / wallet support overview"
source_url: "https://docs.stripe.com/elements/payment-request-button"
category: "general"
---
# Payment Request Button and Digital Wallet Support (Apple & Google Pay)

Stripe provides out-of-the-box support for digital wallet payment methods, including Apple Pay and Google Pay, via the Payment Request Button and Payment Element. No separate merchant accounts or vendor agreements with Apple or Google are required.

To enable Apple Pay and Google Pay:
1. In the Stripe Dashboard under Payment Methods, enable Apple Pay and Google Pay.
2. For web implementations using Apple Pay, register and verify your domain name with Apple via the Stripe Dashboard or API.
3. Integrate the Payment Request Button in your checkout frontend; Stripe.js automatically detects device and browser compatibility and displays the appropriate Apple Pay or Google Pay button natively.
