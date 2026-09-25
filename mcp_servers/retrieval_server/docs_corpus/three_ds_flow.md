---
topic: "3DS authentication flow and confirming PaymentIntents client-side"
source_url: "https://docs.stripe.com/payments/3d-secure"
category: "payments_charges"
---
# 3D Secure Authentication and Client-Side Payment Confirmation

Strong Customer Authentication (SCA) mandates 3D Secure (3DS) authentication for European and high-risk card payments. When a customer initiates a payment requiring authentication, the PaymentIntent transitions to the 'requires_action' status.

To complete the flow, your client-side frontend (using Stripe.js or mobile SDKs) must invoke 'stripe.confirmPayment()' or 'stripe.handleNextAction()'. This renders the issuing bank's authentication modal or redirect. Once the user completes the 3DS challenge, the client receives confirmation and the PaymentIntent transitions to 'succeeded' (or 'processing'). If client-side code fails to handle the 'next_action' response or fails to call confirmPayment after challenge completion, the transaction remains trapped in 'requires_action'.
