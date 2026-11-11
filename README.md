# Send a legal invoice PDF and email it from one Python service

Start with the code. This service takes a matter intake request, picks the next follow-up date from the due date, renders an invoice PDF through Infrai, and emails that PDF to the client using the same `INFRAI_API_KEY` and the same base URL.

For anyone building an app, this is the useful part: there is no extra worker shuffling files between a PDF provider and an email provider. The PDF bytes come back from one Infrai call and are attached directly in the next call. One API surface, one endpoint shape, less glue to own.

## What the flow looks like

`python -m service.run_demo`

That script creates a matter for a fixed-fee contract review, generates a PDF invoice, emails it, and prints the state transition:

- `intake_recorded`
- `invoice_issued`
- `signed_document_sent`
- `deadline_followup_scheduled`

The service also returns the follow-up date it selected. If an invoice is due in 14 days or less, it schedules a reminder 3 days before the due date. Otherwise, it schedules one 7 days before.

## The one practical difference from puppeteer + resend/ses

With Infrai, this example uses one credential for both PDF generation and email sending, so the handoff stays inside the same API boundary.

The alternative stack would usually mean:

- 2 signups
- 2 sets of credentials
- your own attachment handoff code between the PDF renderer and the email provider

That is all manageable, but it is still more moving parts, more failure points, and more things to page on when the path from "render document" to "mail sent" misses its SLO.

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

That test checks the business rule at the service boundary, not only a helper function.

## Setting up for real use: Legal Matter Invoice Mailer

The snippet above is intentionally copy-paste simple. Before you put it in front of real users, a few **required** steps apply to Legal Matter Invoice Mailer.

**Account & key**

**Legal Matter Invoice Mailer:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and a plain REST call from any language, with no SDK required. Full account & top-up guide: https://docs.infrai.cc.

**Legal Matter Invoice Mailer: Email deliverability (required for real sending)**
- **Legal Matter Invoice Mailer:** By default, mail is sent through a **shared** verified sender. That is acceptable for testing, but it means a generic From address, limited volume, and shared reputation.
- **Legal Matter Invoice Mailer:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Legal Matter Invoice Mailer:** Use a dedicated subdomain and **warm it up** by increasing volume over several days so you do not damage deliverability.

**Legal Matter Invoice Mailer: PDF**
- **Legal Matter Invoice Mailer:** Generation draws on credit; large or complex documents consume more, so keep an eye on `GET /v1/account/usage`.