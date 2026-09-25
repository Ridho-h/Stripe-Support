---
topic: "test vs live mode isolation"
source_url: "https://docs.stripe.com/testing"
category: "auth_keys"
---
# Test Mode vs Live Mode Isolation and Behavior

Stripe provides complete architectural isolation between Test Mode and Live Mode. Test mode requests (authenticated via sk_test_... or pk_test_...) interact solely with simulated card networks and virtual financial accounts. No actual credit card transactions occur, no money moves, and zero real-world financial liability is created.

Objects created in Test Mode (such as customers, products, tokens, and payment intents) do not exist in Live Mode and cannot be referenced by live API requests. You can safely trigger test payments using Stripe's published test card numbers (like 4242 4242 4242 4242) to simulate successful authorizations, insufficient funds, 3DS authentication challenges, and card declines without financial risk.
