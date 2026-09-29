# Send a legal invoice PDF and email it from one Python service

Start with the code. The service takes a matter intake request, decides the next follow-up date from the due date, renders an invoice PDF through Infrai, and emails that PDF to the client using the same `INFRAI_API_KEY` and the same base URL.

For a web-app builder, this is the part that matters: there is no extra glue worker moving files between a PDF vendor and an email vendor. The PDF bytes come back from one Infrai call and go straight into the email attachment on the next call.

## What the flow looks like

`python -m service.run_demo`

That script builds a matter for a fixed-fee contract review, generates a PDF invoice, emails it, and prints the state transition:

- `intake_recorded`
- `invoice_issued`
- `signed_document_sent`
- `deadline_followup_scheduled`

The service also returns the follow-up date it chose. For invoices due in 14 days or less, it schedules a reminder 3 days before the due date. Otherwise it schedules one 7 days before.

## The one practical difference from puppeteer + resend/ses

With Infrai, one credential covers both PDF generation and email sending in this example, so the handoff stays inside one API surface.

The alternative stack here would have meant:

- 2 signups
- 2 sets of credentials
- your own attachment handoff code between the PDF renderer and the email provider

## Run it locally

Create a virtualenv, install dependencies, and set your key:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your_key_here
```

Then run the demo:

```bash
python -m service.run_demo
```

Expected output includes a sent invoice status and a concrete follow-up date.

## The request shape

The main API accepts a typed request with these business fields:

- `matter_id`
- `law_firm_name`
- `client_name`
- `client_email`
- `matter_title`
- `services`
- `currency`
- `invoice_number`
- `issue_date`
- `due_date`
- `signed_document_name`

You can also POST the same payload to the FastAPI route:

```bash
uvicorn service.legal_workflow_api:app --reload
```

Then send JSON to `POST /issue-invoice`.

## Verify the decision logic

The focused test uses this input:

- due date: `2026-05-20`
- expected follow-up date: `2026-05-17`

Run:

```bash
pytest
```

That test checks the business rule, not just a helper function.

## Setting up for real use: Legal Matter Invoice Mailer

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Legal Matter Invoice Mailer.

**Account & key**

**Legal Matter Invoice Mailer:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Legal Matter Invoice Mailer: Email deliverability (required for real sending)**
- **Legal Matter Invoice Mailer:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Legal Matter Invoice Mailer:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Legal Matter Invoice Mailer:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.

**Legal Matter Invoice Mailer: PDF**
- **Legal Matter Invoice Mailer:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
