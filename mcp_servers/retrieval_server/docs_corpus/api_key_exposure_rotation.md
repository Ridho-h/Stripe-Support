---
topic: "API key exposure / rotating compromised secret keys"
source_url: "https://docs.stripe.com/keys"
category: "auth_keys"
---
# Compromised API Key Emergency Response and Rotation

If a live secret API key (sk_live_...) is committed to a public repository or exposed, treat it as an active critical security incident. Anyone with access to that key can make unauthorized charges, access customer personal data, and initiate transfers or payouts.

Immediate incident response steps:
1. Immediately navigate to the Stripe Dashboard > Developers > API keys and generate a new secret key.
2. Deploy the new key to your production backend systems.
3. Revoke / delete the compromised secret key from the Dashboard immediately.
4. Review the API request logs in the Dashboard for any unauthorized requests made with the leaked key.
5. Escalate to Stripe Support and your security team if unauthorized funds movement or data exfiltration is suspected.
