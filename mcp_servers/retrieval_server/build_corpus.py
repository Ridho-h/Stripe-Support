import os
import yaml

TARGET_DIR = r"c:\Kerja\Dummy Projects\AI Engineer\Stripe-Support-Agent-Dashboard\mcp_servers\retrieval_server\docs_corpus"
os.makedirs(TARGET_DIR, exist_ok=True)

docs = [
    {
        "filename": "webhook_signing_secret_rotation.md",
        "topic": "webhook signing secret rotation / raw body middleware ordering",
        "category": "webhooks",
        "source_url": "https://docs.stripe.com/webhooks/signatures",
        "content": """# Webhook Signature Verification and Signing Secret Rotation

Stripe validates the integrity and authenticity of webhook payloads using cryptographic HMAC-SHA256 signatures contained in the `Stripe-Signature` HTTP header. Implementing proper verification prevents replay attacks and ensures incoming requests genuinely originate from Stripe.

### Raw Request Body Ordering
The most common cause of verification failure (such as `No signatures found matching the expected signature for payload`) is premature JSON parsing. Signature computation relies strictly on the exact, unmodified byte stream received across the wire. If server middleware such as Express `express.json()` or `bodyParser.json()` parses the request body before invoking Stripe's verification helper (`stripe.webhooks.constructEvent`), whitespace differences, key reordering, or character encodings alter the byte array. Consequently, the computed hash mismatches the header signature. Developers must mount raw body parsers (e.g., `express.raw({ type: 'application/json' })`) specifically on the webhook route prior to any global JSON body-parsing middlewares.

### Secret Key Rotation
Each webhook endpoint is assigned a unique signing secret prefixed with `whsec_`. When updating or rotating a compromised signing secret, navigate to Dashboard > Developers > Webhooks, select the endpoint, and initiate rotation. Stripe supports an automated rollover window (typically 24 hours), during which both the old and new signing secrets remain valid concurrently. This dual-secret grace period permits engineering teams to safely deploy the new secret across server fleets without dropping incoming events or incurring signature verification errors. Once deployment completes, administrators can revoke the previous secret immediately."""
    },
    {
        "filename": "idempotency_keys_payment_intent.md",
        "topic": "idempotency keys for PaymentIntent creation",
        "category": "api_idempotency",
        "source_url": "https://docs.stripe.com/api/idempotent_requests",
        "content": """# Idempotency Keys for PaymentIntent Creation

Network instability, dropped connections, and automatic client retries can lead to accidental duplicate requests. In financial transactions, retrying a charge request without idempotency protections frequently results in double-billing customers.

### How Idempotency Works
Stripe guarantees idempotency for mutating HTTP requests (such as `POST /v1/payment_intents`) through the optional `Idempotency-Key` request header. By supplying a unique client-generated identifier—commonly a UUID v4 or an internal order identifier combined with an attempt index—Stripe tracks the request state. When the Stripe API receives a request bearing an idempotency key that it processed within the preceding 24 hours, it short-circuits execution and returns the cached response, including HTTP status code and response payload, without performing a secondary charge.

### Handling Timeouts and Duplicate Prevention
When initiating payment flows:
1. Always attach an `Idempotency-Key` header before dispatching the PaymentIntent creation request.
2. If a socket timeout or network error occurs, safely retry the exact request with the identical key.
3. If an idempotency conflict occurs because a previous request is still executing, Stripe returns an HTTP 409 status code; clients should retry after a brief delay.

### Addressing Historical Duplicates
If duplicate PaymentIntents were created without idempotency keys, query the PaymentIntents API filtering by customer and creation timestamp, or inspect the Dashboard Payments view. Identify identical charges sharing identical amounts and close timestamps, confirm customer order associations, and issue prompt partial or full refunds (`POST /v1/refunds`) on redundant charges."""
    },
    {
        "filename": "stripe_cli_webhook_forwarding.md",
        "topic": "Stripe CLI webhook forwarding",
        "category": "webhooks",
        "source_url": "https://docs.stripe.com/stripe-cli/webhooks",
        "content": """# Stripe CLI Webhook Forwarding for Local Development

Developing and testing webhook handlers locally requires routing external HTTP callbacks to a localhost development server. The official Stripe CLI eliminates the need for third-party tunneling solutions (such as ngrok) by establishing a secure WebSocket tunnel directly between Stripe and your local environment.

### Setting Up Webhook Forwarding
To begin streaming events to your local application:
1. Authenticate the CLI with your Stripe account using `stripe login`.
2. Start your local web server hosting your webhook listener (e.g., listening on port 4242 at `/webhook`).
3. Run the forwarding command:
   ```bash
   stripe listen --forward-to localhost:4242/webhook
   ```
4. The CLI will output a local webhook signing secret in the terminal formatted as `whsec_...`. Configure this specific secret in your local environment variables (e.g., `STRIPE_WEBHOOK_SECRET`) so that signature verification logic matches incoming local test payloads.

### Triggering and Filtering Events
Developers can test specific failure states and integration flows on demand without manually completing a checkout flow. The CLI allows triggering synthetic test mode events directly:
```bash
stripe trigger payment_intent.succeeded
stripe trigger customer.subscription.created
```
Additionally, you can restrict forwarded traffic to specific event types using the `--events` flag (e.g., `stripe listen --events payment_intent.succeeded,charge.refunded --forward-to localhost:4242/webhook`). All events delivered via CLI forwarding exist strictly within Stripe's isolated test mode."""
    },
    {
        "filename": "payout_delays_verification_holds.md",
        "topic": "payout schedule delays / account verification holds",
        "category": "connect_payouts",
        "source_url": "https://docs.stripe.com/connect/payouts",
        "content": """# Payout Schedule Delays and Account Verification Holds

In Stripe Connect, platforms facilitate disbursements to sellers, service providers, and vendors via connected accounts. When payouts remain stuck in `pending` status for extended periods, the delay typically stems from regulatory verification holds, initial waiting periods, or risk assessments.

### New Account Initial Reserve Period
For newly created connected accounts, Stripe automatically enforces an initial payout waiting period (standardly 7 to 14 business days depending on country and business category). This delay provides a safety window against early fraud and chargebacks while account history is established. Subsequent payouts follow the account's configured payout schedule (e.g., daily rolling, weekly, or manual).

### Compliance Holds and KYC Requirements
Global anti-money laundering (AML) and Know Your Customer (KYC) regulations require Stripe to verify the identity of individuals and legal entities handling funds. Payouts are paused (`payouts_enabled: false`) when required compliance documentation is missing or rejected. To investigate:
1. Retrieve the connected account via the API (`GET /v1/accounts/:id`).
2. Inspect the `requirements` hash, specifically `requirements.currently_due`, `requirements.past_due`, and `requirements.disabled_reason`.
3. Check for requests such as government photo IDs, business registration proof, or beneficial ownership declarations.
4. Direct the connected user to complete onboarding updates via the Stripe-hosted onboarding link or embedded Connect components.

### Risk and Balance Deficits
Elevated dispute rates or negative account balances on connected accounts will also suspend payouts until reserve requirements or platform liability settlements are satisfied."""
    },
    {
        "filename": "subscription_billing_cycle_anchor.md",
        "topic": "subscription billing_cycle_anchor and proration behavior",
        "category": "billing_subscriptions",
        "source_url": "https://docs.stripe.com/billing/subscriptions/billing-cycle",
        "content": """# Subscription Billing Cycle Anchor and Proration Behavior

Stripe Billing dictates recurring invoice schedules through the `billing_cycle_anchor` parameter on the Subscription object. Modifying when customers are invoiced involves adjusting this anchor and configuring how interim service periods are prorated.

### Understanding billing_cycle_anchor
The `billing_cycle_anchor` represents the Unix timestamp that fixes the recurring billing cadence (such as billing on the 1st of every month). When a subscription is initially created without setting an anchor, the anchor defaults to the subscription creation date.

### Adjusting Billing Anchors on Active Subscriptions
When shifting customer billing dates (for example, standardizing all customers to renew on the 1st of the month):
- Update the subscription using `POST /v1/subscriptions/:id`.
- Provide the upcoming target timestamp in `billing_cycle_anchor`. Alternatively, passing `billing_cycle_anchor: 'now'` immediately closes the existing cycle, generates an invoice, and resets the cadence to today's date.
- Specify `proration_behavior` to manage financial adjustments during the gap.

### Managing Proration Behavior
Changing cycle anchors alters the length of the current billing period. Stripe provides three options for `proration_behavior`:
1. `create_prorations` (Default): Stripe calculates a credit for unused time on the old cadence and adds a prorated line item for service until the new anchor date, applying it to the next generated invoice.
2. `always_invoice`: Immediately generates, finalizes, and attempts payment collection on an invoice containing the calculated prorations.
3. `none`: Shifts the anchor date without creating credits or extra charges, effectively forgiving the gap or extending the current term without billing adjustments."""
    },
    {
        "filename": "api_key_exposure_rotation.md",
        "topic": "API key exposure / rotating compromised secret keys",
        "category": "auth_keys",
        "source_url": "https://docs.stripe.com/keys",
        "content": """# Handling API Key Exposure and Rotating Compromised Secret Keys

Accidental exposure of a live secret API key (`sk_live_...` or `rk_live_...`) in public version control repositories, client-side bundles, or publicly accessible logs constitutes an urgent security incident. Anyone possessing a live secret key has administrative read and write privileges over customer records, payment authorizations, and balance transfers.

### Immediate Containment Steps
1. **Revoke and Rotate Immediately**: Navigate to the Stripe Dashboard at **Developers > API keys**. Create a new Secret Key or Restricted Key with least-privilege permissions. During creation, choose whether to revoke the compromised key immediately or set an expiration window (up to 24 hours) for phased server rollouts. If an unauthorized party actively controls the key, revoke it immediately without a rollover period.
2. **Deploy Replacement Credentials**: Update application configuration stores, secret managers (such as AWS Secrets Manager or HashiCorp Vault), and continuous integration pipelines with the newly generated key.
3. **Purge Version Control History**: Deleting a file or making a subsequent commit in Git does not erase commit history. Use tools like `git-filter-repo` or BFG Repo-Cleaner to permanently purge secrets from Git trees, or destroy and re-clone the repository if shared publicly.

### Post-Incident Audit
Inspect Dashboard **Developers > Logs** and the **Events** log filtered by the timeframe of exposure. Audit recent PaymentIntents, customer creations, refunds, and bank account/payout destination updates for unauthorized changes. Report any suspicious transactions immediately to Stripe Support."""
    },
    {
        "filename": "refund_timelines_payment_methods.md",
        "topic": "refund processing timelines by payment method",
        "category": "refunds_disputes",
        "source_url": "https://docs.stripe.com/refunds",
        "content": """# Refund Processing Timelines by Payment Method

When a refund request is submitted through the Stripe Dashboard or API (`POST /v1/refunds`), Stripe submits the refund instruction to the relevant payment network immediately. The status of the Refund object in Stripe transitions to `succeeded`, indicating that Stripe has released the funds. However, the time required for funds to credit the customer's account depends entirely on the underlying payment method and issuing financial institutions.

### Timelines by Payment Rails
- **Credit and Debit Cards**: Typically take **5 to 10 business days** to appear on the customer's statement. Card issuer batch posting cycles and bank holidays can cause delays. In some cases, if the refund was initiated shortly after the original transaction, it may appear as a transaction reversal (void) where the original pending charge drops off the statement entirely rather than appearing as a distinct credit line.
- **Digital Wallets (Apple Pay, Google Pay)**: Wallets pass transactions to the linked credit or debit card; hence, the timeline remains **5 to 10 business days**.
- **Bank Transfers and Direct Debits (ACH, SEPA, Bacs)**: Require **3 to 7 business days** for clearinghouses to reverse the settlement.
- **Local Payment Methods (e.g., iDEAL, Sofort)**: Refund crediting ranges between **2 to 5 business days**.

### Tracing Delayed Refunds
If a cardholder reports no credit after 10 business days:
1. Locate the Acquirer Reference Number (ARN) within the Charge details on the Dashboard.
2. Provide the ARN to the cardholder, who can supply this identifier to their issuing bank's dispute/trace department to track the exact fund settlement."""
    },
    {
        "filename": "dispute_evidence_submission_deadlines.md",
        "topic": "dispute evidence submission and deadlines",
        "category": "refunds_disputes",
        "source_url": "https://docs.stripe.com/disputes/responding",
        "content": """# Dispute Evidence Submission and Deadlines

When a cardholder contests a charge with their issuing bank, a dispute (chargeback) is created, immediately reversing the transaction amount plus a dispute fee from the merchant's balance. Merchants have a single opportunity to challenge the dispute by submitting compelling evidence.

### Submission Deadlines
Payment networks (Visa, Mastercard, American Express) establish strict, legally mandated deadlines for submitting counter-evidence. The submission deadline is specified on the Dispute object as `evidence_details.due_by` (expressed as a Unix timestamp), typically ranging between **7 and 21 calendar days** from the dispute creation date. 
> **Important**: Once this timestamp expires, the payment network closes the dispute permanently. Stripe cannot extend deadlines or submit late evidence on a merchant's behalf.

### Submitting Compelling Evidence
Merchants can submit evidence via the Dashboard (under Payments > Disputes) or programmatically via the API (`POST /v1/disputes/:id`):
1. **Match Dispute Reason**: Review `dispute.reason`. For fraudulent claims or product non-receipt (`product_not_received`), submit clear proof of fulfillment.
2. **Physical Delivery Evidence**: Provide tracking numbers, carrier names, and scanned copies of recipient delivery signatures matching the customer's shipping address.
3. **Digital Goods Evidence**: Submit server access logs, IP addresses, download timestamps, and customer communication demonstrating active utilization.
4. **Formatting**: Ensure files (PDFs, PNGs) are legible, concise, and structured. Card issuers review hundreds of claims daily; highlight relevant clauses in customer terms or cancellation policies.

After submission, the card issuer typically renders a final decision within 60 to 90 days."""
    },
    {
        "filename": "test_vs_live_mode_isolation.md",
        "topic": "test vs live mode isolation",
        "category": "auth_keys",
        "source_url": "https://docs.stripe.com/test-mode",
        "content": """# Test Mode vs Live Mode Isolation in Stripe

Stripe maintains an absolute partition between test mode and live mode. This isolation guarantees that development, testing, and continuous integration environments can execute comprehensive end-to-end payment simulations without moving real currency or impacting production data.

### Key and Environment Separation
Access to each environment is determined solely by the API key provided in the HTTP request:
- **Test Mode Keys**: Publishable keys begin with `pk_test_` and secret keys begin with `sk_test_` (or `rk_test_` for restricted keys).
- **Live Mode Keys**: Publishable keys begin with `pk_live_` and secret keys begin with `sk_live_` (or `rk_live_`).

Requests executed using test API keys interact exclusively with the test sandbox. No real bank accounts, card networks, or financial institutions are ever contacted, and no monetary charges occur.

### Data Partitioning
Data objects are strictly non-transferable between modes:
- A `Customer`, `PaymentIntent`, or `Subscription` created in test mode does not exist in live mode.
- Attempting to pass a test mode object identifier (such as `cus_test123`) to an API call authenticated with a live secret key results in a `404 resource_missing` error.
- Webhook endpoints are separately configured for test mode versus live mode in the Dashboard.

### Simulating Scenarios
Stripe provides special test card numbers that trigger specific outcomes—such as successful authorization, specific decline codes (e.g., `card_declined`, `insufficient_funds`), and 3D Secure challenges—allowing developers to thoroughly validate error handling and webhook execution before deploying to production."""
    },
    {
        "filename": "radar_custom_rules_allow_lists.md",
        "topic": "Radar custom rules and allow lists",
        "category": "radar_fraud",
        "source_url": "https://docs.stripe.com/radar/rules",
        "content": """# Stripe Radar Custom Rules and Allow Lists

Stripe Radar uses machine learning models trained on billions of global transactions to assess fraud risk. To tailor fraud prevention to specific business models, merchants on Radar for Fraud Teams can deploy custom rules and manage Allow lists to prevent false positives on trusted customers.

### Rule Evaluation Hierarchy
Radar evaluates rules sequentially in the following priority order:
1. **Allow Rules**: If an Allow rule matches, the transaction bypasses all subsequent Block and Review rules and proceeds directly to card authorization.
2. **Block Rules**: If a Block rule matches (and no Allow rule triggered), Radar declines the payment before sending it to the card network, avoiding processing and dispute fees.
3. **Review Rules**: Transactions triggering Review rules are authorized but placed in the Dashboard Review queue for manual inspection.

### Addressing False Positives on High-Value Clients
When legitimate enterprise or VIP customers are inadvertently blocked by default ML risk thresholds:
- **Add to Allow List**: Navigate to **Radar > Lists** in the Dashboard. You can add specific card fingerprints, email addresses, IP addresses, or customer IDs to the Allow list.
- **Author Custom Allow Rules**: Define targeted rules that override default blocks, such as:
  ```
  Allow if :customer:email == 'vip-client@enterprise.com'
  Allow if :customer:id == 'cus_12345' and :amount_in_usd: > 10000
  ```
- **Rule Simulation**: Always test custom rules using Radar's backtesting simulator. The simulator analyzes historical transaction data over the past six months to verify that the new rule does not inadvertently allow fraudulent volume."""
    },
    {
        "filename": "stripe_tax_digital_goods.md",
        "topic": "Stripe Tax automatic calculation for digital goods",
        "category": "tax",
        "source_url": "https://docs.stripe.com/tax",
        "content": """# Stripe Tax Automatic Calculation for Digital Goods and SaaS

Businesses selling software, SaaS, and digital goods across international borders face complex indirect tax regulations, including Value Added Tax (VAT) in the European Union, Goods and Services Tax (GST), and United States sales tax. Stripe Tax automates tax calculation, collection, and compliance monitoring.

### How Stripe Tax Operates
When integrated with Stripe Checkout, Invoicing, or the PaymentIntents API (`automatic_tax: { enabled: true }`), Stripe Tax performs automated real-time compliance steps:
1. **Location Determination**: Identifies the buyer's precise jurisdiction using IP address geolocation, billing address, and card issuer BIN data.
2. **Product Tax Categorization**: Matches transactions to Stripe Product Tax Codes. For example, assigning `txcd_10000000` (Software as a Service - business) or `txcd_10010001` (electronically supplied services - consumer) ensures appropriate tax treatment.
3. **Tax ID Validation**: Automatically verifies B2B customer tax IDs (such as EU VAT numbers via the VIES database) and applies reverse-charge mechanisms, exempting tax where legally required.
4. **Nexus Monitoring**: Tracks sales thresholds in each state and country, alerting merchants when revenue exceeds economic nexus limits requiring registration.

### B2B vs B2C EU VAT
For digital services delivered into the EU:
- **B2C Transactions**: The seller must charge destination-based VAT according to the customer's member state rate.
- **B2B Transactions**: If the buyer supplies a valid VAT registration number, Stripe validates the identifier, zeroes the VAT rate, and annotates the invoice with the EU reverse charge notice.

Merchants must register with local tax authorities (or the EU One-Stop Shop / OSS) before remitting collected taxes."""
    },
    {
        "filename": "three_ds_authentication_payment_intents.md",
        "topic": "3DS authentication flow and confirming PaymentIntents client-side",
        "category": "payments_charges",
        "source_url": "https://docs.stripe.com/payments/3d-secure",
        "content": """# 3D Secure (3DS) Flow and Confirming PaymentIntents Client-Side

Strong Customer Authentication (SCA) regulations in the European Economic Area and global fraud prevention protocols require 3D Secure two-factor authentication for card transactions. The PaymentIntents API coordinates this multi-step authentication process between buyer, merchant, and issuing bank.

### The requires_action State
When a customer initiates a payment that triggers 3DS (either due to regulatory requirements or Radar rules):
1. The server creates and confirms a PaymentIntent, or the client confirms it via Stripe.js.
2. If the issuing bank requests biometric verification or an SMS one-time passcode, the PaymentIntent status transitions to `requires_action`.
3. The PaymentIntent object populates `next_action.type = use_stripe_sdk`.

### Handling Client-Side Next Actions
If a PaymentIntent remains stuck in `requires_action`, the frontend application failed to handle the required authentication modal:
- Using **Stripe.js**: Ensure the checkout flow invokes `stripe.confirmCardPayment()` or `stripe.handleNextAction(clientSecret)`. Stripe.js automatically manages displaying the bank's authentication iframe, challenge modal, and biometric popups.
  ```javascript
  const { error, paymentIntent } = await stripe.handleNextAction({
    clientSecret: paymentIntentClientSecret
  });
  if (paymentIntent.status === "requires_confirmation") {
    // Re-confirm on your server if necessary, or let Stripe.js finalize
  }
  ```
- **Webhook Fulfillment**: Client-side network disconnects can interrupt the browser before redirecting to the success page. Always rely on asynchronous backend webhooks (`payment_intent.succeeded` and `payment_intent.payment_failed`) to fulfill orders and update application state rather than relying solely on browser callbacks."""
    },
    {
        "filename": "custom_pricing_sales_routing.md",
        "topic": "custom pricing / sales contact routing",
        "category": "general",
        "source_url": "https://stripe.com/pricing",
        "content": """# Custom Pricing and Enterprise Sales Contact Routing

Stripe offers transparent standard pricing for businesses of all sizes (standardly 2.9% + 30¢ per successful card charge in the United States). However, high-growth companies, platforms, and large enterprises with significant transaction volumes may qualify for customized pricing structures.

### Qualification for Custom Pricing
Custom pricing arrangements are evaluated based on several commercial criteria:
- **Processing Volume**: Typically intended for companies processing over $100,000 to $1,000,000+ in annual or monthly card volume.
- **Specialized Business Models**: Companies operating microtransaction platforms with low average order values (AOVs), high-ticket B2B transactions, or multi-currency global market presence.
- **Product Suite Bundling**: Large-scale utilization across multiple Stripe products, such as Stripe Connect, Billing, Radar for Fraud Teams, and Stripe Tax.

### Custom Pricing Structures
Enterprise contracts may include:
- **Interchange-Plus Pricing**: Charges the exact underlying card network interchange fee plus a fixed, transparent Stripe processing markup, offering substantial savings on debit and commercial cards.
- **Volume Tier Discounts**: Sliding scale discounts that reduce marginal processing fees as transaction volumes scale.
- **Dedicated Support & SLAs**: Access to technical account managers, priority support routing, and dedicated implementation architects.

### How to Engage Sales
Support engineers and automated triage agents cannot negotiate fee rates directly. Inquiries regarding custom rate reviews, volume discounting, or contract renewals must be routed to Stripe's Enterprise Sales team via the official contact form at `stripe.com/contact/sales` or escalated internally to assigned Account Executives."""
    },
    {
        "filename": "trial_end_webhooks_invoice_timing.md",
        "topic": "trial_end webhook events and invoice generation timing",
        "category": "billing_subscriptions",
        "source_url": "https://docs.stripe.com/billing/subscriptions/trials",
        "content": """# Trial End Webhooks and Invoice Generation Timing

Stripe Billing enables businesses to offer trial periods on subscription plans. Understanding the precise lifecycle events and timing of automated invoice generation prevents misunderstandings regarding billing execution.

### Upcoming Expiration Notification
Three days before a customer's trial period concludes, Stripe dispatches the `customer.subscription.trial_will_end` webhook event. This notification provides an opportunity for applications to send reminder emails to subscribers regarding upcoming billing or prompt them to add a payment method if none is on file.

### Trial Expiration and Invoice Finalization
When the timestamp configured in `trial_end` arrives:
1. The subscription's `status` changes from `trialing` to `active`.
2. Stripe automatically creates the initial renewal invoice in a `draft` state, firing the `invoice.created` event.
3. **One-Hour Grace Window**: By default, Stripe holds invoices in `draft` status for approximately one hour before finalization. This buffer allows webhook handlers or backend scripts to append additional usage charges, apply coupons, or add invoice line items before payment collection.
4. Once finalized, Stripe issues `invoice.finalized` and attempts payment collection against the customer's default payment method.
5. Upon successful settlement, Stripe fires `invoice.paid` and `payment_intent.succeeded`.

### Common Misconceptions
Subscribers often expect immediate charges at the exact second the trial expires. Because of the draft finalization window and asynchronous payment processing queues, invoices may take 1 to 2 hours following `trial_end` to post charges. Integrations should monitor `invoice.paid` rather than assuming immediate charge execution."""
    },
    {
        "filename": "invoice_pdf_export_api_dashboard.md",
        "topic": "invoice PDF export via API vs dashboard",
        "category": "general",
        "source_url": "https://docs.stripe.com/invoicing/overview",
        "content": """# Exporting Invoice PDFs via API vs Stripe Dashboard

Finance and accounting teams often need to export past invoices for quarterly tax reconciliation, audit filings, and financial reporting. Stripe provides distinct capabilities and limitations when retrieving invoice PDFs through the Dashboard versus the REST API.

### Dashboard Export Capabilities
Within the Stripe Dashboard under **Billing > Invoices**:
- Users can view and manually download individual invoice PDFs by opening any invoice and clicking **Download PDF** (or **Download receipt**).
- Clicking the **Export** button at the top right of the Invoices table allows users to generate a consolidated CSV export of invoice line items, tax details, and payment statuses over custom date ranges.
- **Bulk PDF Limitation**: The Stripe Dashboard UI does not provide a native one-click button to download hundreds of rendered PDF documents as a single bulk `.zip` archive. Bulk downloads are restricted to tabular CSV reports.

### Bulk PDF Retrieval via the API
To retrieve actual rendered PDF documents in bulk, developers should utilize the Stripe API:
1. Call `GET /v1/invoices` with query parameters such as `created[gte]`, `created[lte]`, and `limit=100`, paginating through results using `starting_after`.
2. Each Invoice object returned contains two direct PDF URL properties:
   - `invoice_pdf`: A secure hosted link to the printable invoice document.
   - `hosted_invoice_url`: A Stripe-hosted interactive page where customers can pay or view receipts.
3. Write a script to fetch each `invoice_pdf` URL and save the binary files to local storage or an S3 bucket."""
    },
    {
        "filename": "connect_application_fees_responsibility.md",
        "topic": "application fees and fee responsibility in Connect",
        "category": "connect_payouts",
        "source_url": "https://docs.stripe.com/connect/direct-charges",
        "content": """# Application Fees and Fee Responsibility in Stripe Connect

Stripe Connect empowers platforms to facilitate payments between buyers and third-party connected accounts while monetizing transactions through application fees. Understanding fee allocation depends on the chosen charge architecture.

### Application Fee Mechanics
Platforms collect platform revenue by specifying the `application_fee_amount` integer parameter (in minor currency units, e.g., cents) when creating a charge or PaymentIntent. Upon settlement, Stripe immediately deposits the application fee into the platform's account balance, transferring the remaining funds to the connected account.

### Charge Types and Fee Responsibility
1. **Direct Charges**:
   - The connected account is the merchant of record. The transaction appears on the connected account's statement.
   - **Stripe Fee Responsibility**: By default, the connected account pays Stripe's card processing fees out of their charge proceeds. The platform receives the exact `application_fee_amount` requested.
   - The platform can optionally set `application_fee_amount` or leverage `transfer_data`.

2. **Destination Charges**:
   - The platform account is the merchant of record. The transaction occurs on the platform, and funds are automatically transferred to the connected account.
   - **Stripe Fee Responsibility**: The platform pays Stripe's processing fees by default. Stripe fees are deducted directly from the platform's balance. The platform retains `application_fee_amount` while net proceeds transfer to the connected seller.

3. **Separate Charges and Transfers**:
   - The platform charges the customer directly and later disburses funds to one or more connected accounts using the Transfers API. The platform incurs all Stripe processing fees and assumes full dispute liability."""
    },
    {
        "filename": "api_rate_limits_bulk_migration.md",
        "topic": "API rate limits and bulk data migration strategies",
        "category": "api_idempotency",
        "source_url": "https://docs.stripe.com/rate-limits",
        "content": """# API Rate Limits and Bulk Data Migration Strategies

When migrating large datasets—such as importing thousands of customer profiles, payment methods, or legacy subscriptions—unthrottled batch scripts frequently encounter HTTP `429 Too Many Requests` errors. Implementing proper throttling and migration strategies ensures efficient data transfer without service disruption.

### Stripe API Rate Limits
Stripe enforces default global rate limits based on account mode:
- **Live Mode**: Standard limit is **100 read requests per second** and **100 write requests per second**.
- **Test Mode**: Enforces a lower threshold of **25 requests per second**.
Bursts exceeding these thresholds trigger HTTP 429 status codes with a `RateLimitError`.

### Best Practices for Scripted Imports
1. **Exponential Backoff with Jitter**: When receiving an HTTP 429 response, do not immediately retry. Implement exponential backoff combined with randomized jitter to prevent synchronized retry storms across concurrent workers.
2. **Client-Side Concurrency Throttling**: Limit concurrent HTTP connection pools. Rather than launching hundreds of unbounded parallel threads, process records using a managed worker queue capped at 20-30 concurrent workers.
3. **Inspect Rate Limit Headers**: Monitor the `Ratelimit-Limit` and `Ratelimit-Remaining` headers to dynamically adjust request velocity.

### Dedicated Data Migration Support
For migrating sensitive PCI-compliant payment card data from another payment gateway, **do not attempt to tokenize raw card numbers through the standard API**, as this violates PCI-DSS regulations. Instead, contact Stripe's Data Migration team. Stripe provides secure, server-to-server bulk migration pipelines to securely import payment credentials directly into your account's Customer vault."""
    },
    {
        "filename": "dispute_monitoring_program_consequences.md",
        "topic": "dispute/chargeback monitoring program consequences",
        "category": "refunds_disputes",
        "source_url": "https://docs.stripe.com/disputes/monitoring-programs",
        "content": """# Card Network Dispute Monitoring Programs and Consequences

Card networks such as Visa and Mastercard operate strict dispute monitoring programs—specifically Visa Dispute Monitoring Program (VDMP), Visa Fraud Monitoring Program (VFMP), and Mastercard Excessive Chargeback Program (ECP). When a merchant's dispute ratio crosses defined thresholds, serious operational and financial consequences follow.

### Dispute Ratio Calculation
Dispute ratios are calculated by dividing the total count of disputes in a calendar month by the total count of successful sales transactions in that same month (or transaction amount for fraud programs). 
- **Standard Warning Threshold**: Approximately **0.65% to 0.75%** dispute ratio and 75-100 disputes.
- **Excessive / Violation Threshold**: Typically **0.90% to 1.00%+** dispute ratio and 100+ disputes.

### Consequences of Program Placement
Crossing into excessive monitoring programs results in escalating penalties:
1. **Heavy Monthly Fines**: Card networks assess substantial compliance fines starting at $50 per dispute, escalating up to thousands of dollars per month the longer an account remains non-compliant.
2. **Additional Interchange Surcharges**: Surcharges of $5 to $10+ per transaction may be levied.
3. **Rolling Reserves**: Stripe and card networks may impose rolling reserves, holding back 10% to 30% of daily processing volume to cover dispute exposure.
4. **Account Termination**: Continued non-compliance typically leads to immediate processing termination and placement on the MATCH/TMF list.

### Immediate Remediation Actions
- Author custom Radar rules to block high-risk transactions.
- Implement pre-dispute alert networks (e.g., Ethoca and Verifi / Rapid Dispute Resolution) to issue immediate refunds before disputes formalize.
- Offer transparent cancellation and refund flows to dissatisfied customers."""
    },
    {
        "filename": "webhook_delivery_ordering_guarantees.md",
        "topic": "webhook delivery ordering guarantees (or lack thereof)",
        "category": "webhooks",
        "source_url": "https://docs.stripe.com/webhooks",
        "content": """# Webhook Delivery Ordering Guarantees and Best Practices

Developers frequently construct webhook listeners assuming events arrive chronologically in the exact order actions occurred in Stripe. However, Stripe **does not guarantee event delivery ordering**.

### Why Events Arrive Out of Order
Stripe utilizes a distributed, highly scalable asynchronous architecture to dispatch webhook notifications. Due to concurrent processing, network latency variations, or transient endpoint failures triggering automated retries, events can arrive out of chronological sequence. For example, an application may receive an `invoice.paid` event prior to receiving `invoice.created`, or a `payment_intent.succeeded` event before `payment_intent.created`.

### Building Resilient Webhook Endpoints
To handle non-linear event arrival without corrupting internal state machines:
1. **Make Handlers Idempotent**: Webhook endpoints should safely handle duplicate and out-of-order deliveries. Store processed `event.id` values in your database to prevent duplicate side effects.
2. **Do Not Rely on Event Timestamps Alone**: While `event.created` indicates when Stripe recorded the event, inspecting an event payload alone may reflect stale state if an object was updated subsequent to that event's dispatch.
3. **Fetch Latest Object State**: When receiving a state-dependent webhook, query the Stripe API directly (e.g., `stripe.paymentIntents.retrieve(event.data.object.id)`) to inspect the ground-truth status of the resource rather than relying exclusively on the event payload.
4. **Guard State Transitions**: Ensure your database updates ignore transitions that regress record status (e.g., do not allow an arriving `payment_intent.created` event to overwrite an already `completed` order status)."""
    },
    {
        "filename": "account_closure_subscription_data_impact.md",
        "topic": "account closure and subscription/data handling implications",
        "category": "billing_subscriptions",
        "source_url": "https://docs.stripe.com/account/close",
        "content": """# Account Closure: Subscription and Data Handling Implications

Closing a Stripe account is a permanent operational action with immediate effects across billing pipelines, active customer subscriptions, and financial data retention.

### Immediate Effects of Closure
When an account owner closes a Stripe account via the Dashboard or API:
- **Payment Processing Terminated**: All active API keys are immediately revoked, and the account can no longer accept payments, create charges, or initiate payouts.
- **Active Subscriptions Canceled**: All active recurring subscriptions managed by Stripe Billing are terminated automatically. Automated renewal invoices cease, and future billing runs will not execute.
- **Pending Payouts**: Payouts already in flight to the verified bank account will generally complete. However, remaining available balances may be held in reserve for up to 180 days to cover potential customer chargebacks, refunds, or outstanding fees.

### Customer Data and Regulatory Retention
Businesses cannot immediately purge all account data upon closure due to legal and compliance requirements:
- **Financial Compliance Retention**: Under global anti-money laundering (AML), Know Your Customer (KYC), and tax reporting statutes, Stripe is legally required to retain transaction records, customer identification data, and payment logs for statutory audit periods (commonly 5 to 7 years).
- **Dashboard Access**: Account administrators retain restricted, read-only access to historical financial reports, invoices, and year-end tax forms (such as 1099-K) through the Dashboard.
- **Exporting Data**: Before initiating closure, merchants should export all customer profiles, payment logs, and invoice histories via Dashboard CSV reports or API backups, as post-closure export capabilities are restricted."""
    },
    {
        "filename": "payment_request_button_wallets.md",
        "topic": "Payment Request Button / wallet support overview",
        "category": "general",
        "source_url": "https://docs.stripe.com/elements/payment-request-button",
        "content": """# Payment Request Button and Digital Wallet Support Overview

Stripe provides built-in support for popular digital wallet payment methods—including Apple Pay, Google Pay, and Link—without requiring separate merchant accounts or distinct acquiring relationships. Integrating wallet checkouts optimizes conversion rates by allowing customers to authorize payments using stored biometrics and device credentials.

### How the Payment Request Button Works
Stripe Elements includes the **Payment Request Button** (and the modern unified **Payment Element**), a dynamic UI component that automatically detects buyer device and browser capabilities:
- On Safari running on iOS or macOS with a configured Apple Wallet, the element displays the official **Apple Pay** button.
- On Chrome running on Android, Windows, or macOS with saved Google Wallet cards, the element renders the **Google Pay** button.
- Across supported browsers, Stripe's one-click checkout system **Link** is displayed if configured.

If a customer's environment does not support any digital wallet, the button automatically hides itself, allowing traditional card input fields to take precedence.

### Domain Verification Requirements
To process live Apple Pay transactions on the web:
1. Register and verify your web domain inside the Stripe Dashboard under **Settings > Payment methods > Apple Pay**.
2. Download the Apple developer merchant association verification file provided by Stripe and host it on your production server at `/.well-known/apple-developer-merchantid-domain-association`.
3. Ensure your site serves traffic exclusively over HTTPS. Google Pay does not require hosted domain association files but requires HTTPS in production."""
    },
    {
        "filename": "charge_object_refund_fields.md",
        "topic": "Charge object refund fields (amount_refunded vs amount)",
        "category": "refunds_disputes",
        "source_url": "https://docs.stripe.com/api/charges/object",
        "content": """# Charge Object Refund Fields: amount_refunded vs amount

When managing partial refunds via the Stripe API or interpreting webhook payloads, developers sometimes encounter confusion regarding how monetary totals are represented on the underlying `Charge` object.

### Immutability of the amount Field
On any Stripe `Charge` object, the `amount` attribute represents the **original gross transaction amount** authorized and captured, expressed in minor currency units (such as cents for USD or EUR). 
> **Key Principle**: The `amount` property is immutable. When a refund occurs—whether partial or full—the `amount` field does **not** decrease.

### Understanding Refund Attributes
To accurately determine refund statuses and calculate remaining balances, inspect the following properties:
- `amount_refunded`: An integer tracking the cumulative total refunded to date. For example, if a customer is charged $100.00 (`amount: 10000`) and receives a partial refund of $20.00, `amount` remains `10000`, while `amount_refunded` becomes `2000`.
- `refunded`: A boolean indicator that remains `false` as long as any unrefunded balance remains. It flips to `true` only when `amount_refunded == amount`.
- `refunds`: A list object containing detailed child `Refund` records, each detailing individual refund timestamps, failure reasons, and status values.

### Calculating Remaining Refundable Balance
To compute the remaining amount available for refund in application code, calculate:
```python
remaining_refundable = charge.amount - charge.amount_refunded
```
Never attempt to calculate balances by expecting `charge.amount` to reflect net proceeds."""
    },
    {
        "filename": "account_security_incident_response_2fa.md",
        "topic": "account security incident response / 2FA enforcement",
        "category": "auth_keys",
        "source_url": "https://docs.stripe.com/security",
        "content": """# Account Security Incident Response and 2FA Enforcement

Detecting unrecognized IP addresses, suspicious logins, or unexpected configuration changes in the Stripe Dashboard demands an immediate security response to safeguard funds, customer records, and API credentials.

### Immediate Containment Checklist
If unauthorized account access is suspected:
1. **Revoke Active Team Sessions**: Sign in as the account Owner, navigate to **Settings > Team**, and review all active members. Revoke any unfamiliar accounts and force sign-out across all current browser sessions.
2. **Rotate All API Keys and Webhooks**: Compromised dashboard accounts may have exposed secret keys or created rogue webhook listeners. Immediately generate replacement secret keys and delete any unauthorized keys or webhook endpoints in **Developers > API keys**.
3. **Inspect Payout Destinations**: Attackers commonly attempt to redirect payout bank accounts. Navigate to **Settings > Bank accounts and scheduling** to verify that external bank account routing numbers and debit card destinations have not been altered.
4. **Halt Payouts if Compromised**: Temporarily pause manual payouts in the Dashboard to prevent funds from being drained while investigating.

### Enforcing Two-Factor Authentication (2FA)
To prevent credential stuffing and password-based account takeovers:
- Navigate to **Settings > Team** and toggle on **Require two-factor authentication for all team members**.
- Require team members to authenticate using hardware security keys (FIDO2/WebAuthn) or time-based one-time password (TOTP) authenticator apps rather than SMS.
- Promptly report suspected breaches to Stripe Security Support."""
    },
    {
        "filename": "provincial_tax_rates_address_validation.md",
        "topic": "provincial tax rates and address validation for Stripe Tax",
        "category": "tax",
        "source_url": "https://docs.stripe.com/tax/canada",
        "content": """# Canadian Provincial Tax Rates and Address Validation for Stripe Tax

Calculating indirect tax in Canada requires navigating a dual federal-provincial system comprising federal Goods and Services Tax (GST), combined Harmonized Sales Tax (HST), and distinct Provincial Sales Tax (PST/QST).

### Canadian Tax Structures by Province
Depending on the customer's province:
- **HST Participating Provinces**: Ontario applies **13% HST**, while New Brunswick, Newfoundland and Labrador, Nova Scotia, and Prince Edward Island apply **15% HST**. HST replaces separate federal and provincial taxes with a single unified rate.
- **GST + PST Provinces**: British Columbia, Manitoba, and Saskatchewan charge federal **5% GST** plus local **6% to 7% PST**.
- **Quebec**: Applies federal **5% GST** plus **9.975% QST**.
- **Non-PST Jurisdictions**: Alberta, Northwest Territories, Nunavut, and Yukon collect only the **5% GST**.

### Why an Ontario Customer May Be Charged 5% GST Instead of 13% HST
When Stripe Tax incorrectly assesses only 5% GST on an Ontario order, the discrepancy typically traces to two root causes:
1. **Missing or Incomplete Address Data**: Stripe Tax requires both a valid Canadian province code (`ON`) and a valid 6-character Canadian Postal Code (e.g., `M5V 2T6`). If the postal code is omitted, malformed, or unverified, Stripe Tax falls back to baseline federal 5% GST because it cannot definitively localize the buyer to Ontario.
2. **Registration Settings in Stripe**: Stripe Tax only collects provincial taxes if the merchant has added an active tax registration for that specific province in **Settings > Tax > Registrations**. If only a federal Canada GST/HST registration is active, Stripe calculates tax only in provinces where that registration applies."""
    },
    {
        "filename": "api_request_log_retention.md",
        "topic": "API request log retention period",
        "category": "general",
        "source_url": "https://docs.stripe.com/logs",
        "content": """# Stripe API Request Log Retention Periods and Archival

The Stripe Dashboard provides a comprehensive API log viewer under **Developers > Logs**, recording every inbound HTTP request, method, endpoint URL, query parameters, request headers, request payloads, response status codes, and response bodies. These logs serve as an indispensable tool for diagnosing integration bugs and verifying webhook handling.

### Standard Retention Window
Stripe retains complete API request logs for a rolling period of **30 days** in both live mode and test mode:
- Requests older than 30 days are automatically purged from Dashboard search results and log details.
- Purged request logs cannot be restored, replayed, or retrieved by Stripe Customer Support.
- High-level financial reporting records (such as completed charges, refunds, transfers, and balance transactions) remain stored indefinitely and are unaffected by API log purging.

### Archival Strategies for Historical Auditing
Organizations with stringent compliance requirements, extended audit lifecycles, or long-term debugging needs must implement external log archival pipelines:
1. **Webhook Event Ingestion**: Stripe Events (e.g., `payment_intent.succeeded`) are retained for 30 days in the Dashboard. Ingest all webhook events into an internal database, cloud data warehouse (such as BigQuery or Snowflake), or message queue.
2. **Client-Side Request Logging**: Wrap the Stripe SDK or HTTP client with logging middleware to record request IDs, idempotency keys, request bodies, response payloads, and latency to an internal log management system (e.g., Datadog, CloudWatch, or Elasticsearch).
3. **Stripe Sigma / Data Pipeline**: Deploy Stripe Data Pipeline to continuously sync complete Stripe data directly into your cloud data warehouse."""
    },
    {
        "filename": "radar_risk_rules_country_tuning.md",
        "topic": "Radar risk rules by country and custom rule tuning",
        "category": "radar_fraud",
        "source_url": "https://docs.stripe.com/radar/rules/country",
        "content": """# Radar Risk Rules by Country and Custom Rule Tuning

Global merchants operating in emerging markets or cross-border jurisdictions often experience elevated false-positive decline rates from default fraud detection heuristics. Stripe Radar evaluates global risk signals, but merchants can tune rules to balance fraud prevention with legitimate regional business operations.

### Understanding Geographic Risk Scores
Stripe Radar evaluates fraud risk based on machine learning models trained on data from across the global Stripe network. Factors such as cross-border issuance, card issuing country, IP geolocation, proxy usage, and mismatched billing origins contribute to the assigned `risk_score` (0 to 99). In certain countries (such as Nigeria, Brazil, or Indonesia), high baseline fraud rates across the payment network can cause legitimate local transactions to trigger default block thresholds (`risk_level: 'highest'`).

### Tuning Rules for Specific Operating Countries
Merchants legitimately conducting business in these regions should customize their Radar rules rather than disabling fraud screening entirely:
1. **Author Granular Allow or Review Rules**: Instead of an outright block on elevated risk scores, create rules that evaluate additional positive authentication indicators:
   ```
   Allow if :card_country: == 'NG' and :is_3d_secure: and :risk_score: < 85
   Review if :card_country: == 'NG' and :risk_score: >= 85
   ```
2. **Mandate 3D Secure**: 3DS provides cryptographic two-factor authentication from the issuing bank and shifts chargeback liability for fraud away from the merchant. Require 3DS for all transactions originating from specific high-risk jurisdictions.
3. **Leverage Customer History**: Author rules allowing transactions if the customer ID has established successful payment history over 60+ days."""
    },
    {
        "filename": "api_versioning_webhook_pinning.md",
        "topic": "API versioning and webhook endpoint version pinning",
        "category": "api_idempotency",
        "source_url": "https://docs.stripe.com/api/versioning",
        "content": """# Stripe API Versioning and Webhook Endpoint Version Pinning

Stripe utilizes date-based API versioning (such as `2020-08-27` or `2024-06-20`) to introduce enhancements and schema modifications without breaking backwards compatibility for existing merchant integrations. Understanding how API versioning affects webhook endpoints prevents unexpected payload formatting errors.

### Default Account Version vs Request Version
- **Default Account Version**: Configured in the Dashboard under **Developers > Overview**. Outbound API calls that do not explicitly define a version header execute using this account default version.
- **Request Header Version**: Applications can override the default version per HTTP request by setting the `Stripe-Version: YYYY-MM-DD` header, allowing teams to test newer schemas incrementally.

### Webhook Endpoint Version Pinning
A crucial architectural distinction in Stripe is that **webhook endpoints do not automatically adopt your account's default API version**:
- When you create a webhook endpoint, it is permanently pinned to the account default version in effect at the moment of creation, or to the specific version chosen during endpoint setup.
- Upgrading your account's default API version in the Dashboard does **not** alter the payload schemas sent to existing webhook endpoints.
- Consequently, upgrading your API version will not break your production webhook handlers.

### Updating Webhook Endpoint Versions
To update a webhook endpoint to a newer schema:
1. Navigate to **Developers > Webhooks** and select the target endpoint.
2. Review breaking changes associated with the newer version.
3. Update your local webhook ingestion code to handle modified fields.
4. Click **Upgrade** on the endpoint within the Dashboard."""
    },
    {
        "filename": "connect_identity_verification_failures.md",
        "topic": "identity verification failures in Connect onboarding",
        "category": "connect_payouts",
        "source_url": "https://docs.stripe.com/connect/identity-verification",
        "content": """# Identity Verification Failures in Connect Onboarding

Stripe Connect requires connected account owners and platform sellers to undergo identity verification to comply with Know Your Customer (KYC), anti-money laundering (AML), and tax reporting requirements. Automated verification errors during onboarding frequently delay payouts.

### Common Causes of Verification Rejection
When an individual's Social Security Number (SSN), Individual Taxpayer Identification Number (ITIN), or national ID is rejected during onboarding:
1. **Data Mismatches**: The entered legal name, date of birth, and home address must match official government databases (such as the Social Security Administration or credit bureaus) exactly. Common errors include using nicknames, shortened middle names, transposed digits in birth dates, or unupdated residential addresses.
2. **Recent Legal Name or Address Changes**: Recent marriages, name changes, or address moves may not yet be reflected in credit bureau verification databases.
3. **Entity vs Individual Confusion**: For company accounts, entering an individual's personal SSN in place of a corporate Employer Identification Number (EIN), or vice versa, causes instant verification mismatches.

### Resolving Verification Blocks
When automated checks fail:
- Query the Account object via the API (`GET /v1/accounts/:id`) and inspect `requirements.errors`. Each error object includes a `code`, `reason`, and the affected `requirement` key.
- Stripe automatically falls back to secondary verification, requiring the user to upload clear color photographs of a government-issued photo ID (driver's license or passport) and proof of address (utility bill or bank statement).
- Direct connected accounts to upload documents via Stripe-hosted Connect onboarding or the Dashboard verification portal."""
    },
    {
        "filename": "api_version_changelog_upgrades.md",
        "topic": "API version changelog / upgrade guide",
        "category": "general",
        "source_url": "https://docs.stripe.com/upgrades",
        "content": """# Stripe API Version Changelog and Upgrade Guide

Stripe continuously refines its REST API, introducing new features, deprecating obsolete properties, and optimizing schemas through dated API releases. The official API Changelog and Upgrade Guide provides comprehensive documentation of every breaking change between releases.

### Accessing the API Changelog
The authoritative documentation for all breaking and non-breaking API changes is hosted at `docs.stripe.com/upgrades`. Developers planning an API upgrade should review this changelog to evaluate differences between their current pinned version and the target release. Each changelog entry outlines:
- Deprecated, renamed, or relocated response properties and request parameters.
- Behavioral modifications in billing, payment confirmation states, and tax calculations.
- Schema changes in webhook event payloads.

### Recommended Upgrade Workflow
Upgrading an existing integration should always follow a structured, phased rollout:
1. **Review Differences**: In the Stripe Dashboard under **Developers > API version**, view your current default version and read the highlighted breaking changes.
2. **Test via Headers in Staging**: Rather than immediately switching your account's global default version, test the new API version in your development environment by passing the `Stripe-Version: YYYY-MM-DD` HTTP request header on SDK client instances.
3. **Audit Webhooks Separately**: Verify whether webhook handlers expect deprecated fields. Create a dedicated test webhook endpoint pinned to the target version to validate event handling.
4. **Switch Default Version**: Once test suites pass cleanly, update your account's default API version in the Dashboard. Previous API versions remain available indefinitely via explicit header specification."""
    },
    {
        "filename": "decline_codes_invoice_failure_reasons.md",
        "topic": "decline codes and reading detailed failure reasons on invoices",
        "category": "billing_subscriptions",
        "source_url": "https://docs.stripe.com/declines",
        "content": """# Card Decline Codes and Detailed Failure Reasons on Recurring Invoices

When an automated recurring subscription payment fails, Stripe marks the invoice as `open` and sets the invoice's `attempt_count`. In the Dashboard and webhooks, the high-level error often surfaces simply as `card_declined`. Uncovering the precise bank refusal reason is essential for resolving customer payment issues.

### Inspecting the Underlying Charge Outcome
An invoice does not execute card transactions directly; rather, it generates a `PaymentIntent` and a corresponding `Charge`. To diagnose the exact failure reason:
1. Retrieve the Invoice via the API (`GET /v1/invoices/:id`) and locate the `payment_intent` or `charge` ID.
2. Retrieve the Charge object and inspect the `outcome` dictionary:
   - `outcome.network_status`: Indicates whether the card issuer or Stripe's risk engine declined the payment.
   - `outcome.reason`: High-level decline category.
   - `outcome.seller_message`: A descriptive explanation detailing why the payment failed.
   - `outcome.network_decline_code`: The raw alphanumeric code returned by the cardholder's issuing bank (e.g., `insufficient_funds`, `do_not_honor`, `transaction_not_allowed`, `expired_card`).

### Customer-Side Resolution
Cardholders frequently state that their card works normally for other retail purchases even when recurring subscription billing fails. Issuing banks apply specialized fraud algorithms to card-not-present, automated recurring subscription charges:
- `do_not_honor` / `generic_decline`: The bank's security system blocked the automated transaction. The customer must contact their issuing bank directly to explicitly authorize recurring charges from your merchant identifier.
- `insufficient_funds`: The account lacked sufficient credit or balance at the time of the automated charge attempt."""
    }
]

print(f"Total documents defined: {len(docs)}")

files_created = []

for doc in docs:
    filepath = os.path.join(TARGET_DIR, doc["filename"])
    
    # Generate YAML frontmatter
    frontmatter = {
        "topic": doc["topic"],
        "source_url": doc["source_url"],
        "category": doc["category"]
    }
    frontmatter_str = yaml.dump(frontmatter, sort_keys=False).strip()
    
    full_text = f"---\n{frontmatter_str}\n---\n\n{doc['content'].strip()}\n"
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_text)
        
    # Count words in markdown content (excluding frontmatter)
    words = len(doc["content"].split())
    files_created.append((doc["filename"], doc["topic"], doc["category"], words))

print("\nValidation Summary:")
for fname, topic, cat, wc in files_created:
    print(f"[{cat}] {fname} ({wc} words) - {topic}")

print(f"\nSuccessfully generated {len(files_created)} files.")
