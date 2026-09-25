---
topic: "invoice PDF export via API vs dashboard"
source_url: "https://docs.stripe.com/invoicing/overview"
category: "general"
---
# Invoice PDF Export Methods via Dashboard and API

Stripe generates downloadable PDF receipts and invoices for all finalized invoice objects. In the Stripe Dashboard under Invoices, merchants can search and export invoice records as CSV reports, but bulk downloading thousands of rendered PDF files directly from the UI is not natively supported in a single click.

To export invoice PDFs in bulk for accounting or archival purposes, developers should utilize the Stripe Invoices API. By iterating through the 'GET /v1/invoices' list endpoint, each invoice object contains an 'invoice_pdf' field with a hosted link directly to the rendered PDF file. An automated script can fetch these URLs and download the PDF documents systematically.
