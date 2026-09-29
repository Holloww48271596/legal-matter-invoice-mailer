from __future__ import annotations

import base64
from datetime import timedelta
from decimal import Decimal

from .infrai_client import InfraiClient
from .models import MatterIntakeRequest, WorkflowResult


class LegalInvoiceWorkflow:
    def __init__(self, infrai: InfraiClient):
        self.infrai = infrai

    def issue_invoice(self, request: MatterIntakeRequest) -> WorkflowResult:
        total = sum((line.quantity * line.unit_price for line in request.services), start=Decimal("0"))
        follow_up_date = self._choose_follow_up_date(request)
        html = self._build_invoice_html(request, total, follow_up_date.isoformat())

        pdf_response = self.infrai.pdf_generate(html=html, page_size="A4", orientation="portrait", store=False)
        pdf_data = pdf_response["data"]
        pdf_base64 = pdf_data["pdf_base64"]
        pdf_bytes = base64.b64decode(pdf_base64)

        email_html = self._build_email_html(request, total)
        email_response = self.infrai.email_send(
            to=request.client_email,
            subject=f"Invoice {request.invoice_number} for {request.matter_title}",
            html=email_html,
            attachments=[
                {
                    "filename": f"{request.invoice_number}.pdf",
                    "content_base64": self.infrai.as_base64(pdf_bytes),
                    "content_type": "application/pdf",
                }
            ],
        )

        status_history = [
            "intake_recorded",
            "invoice_issued",
            "signed_document_sent",
            "deadline_followup_scheduled",
        ]

        return WorkflowResult(
            matter_id=request.matter_id,
            invoice_number=request.invoice_number,
            total_amount=f"{total:.2f}",
            currency=request.currency,
            follow_up_date=follow_up_date,
            status_history=status_history,
            pdf_bytes=pdf_bytes,
            email_message_id=email_response["data"]["message_id"],
        )

    def _choose_follow_up_date(self, request: MatterIntakeRequest):
        days_until_due = (request.due_date - request.issue_date).days
        lead_days = 3 if days_until_due <= 14 else 7
        return request.due_date - timedelta(days=lead_days)

    def _build_invoice_html(self, request: MatterIntakeRequest, total: Decimal, follow_up_iso: str) -> str:
        lines_html = "".join(
            f"<tr><td>{line.description}</td><td>{line.quantity}</td><td>{line.unit_price:.2f}</td><td>{(line.quantity * line.unit_price):.2f}</td></tr>"
            for line in request.services
        )
        return f"""
        <html>
          <body style=\"font-family: Arial, sans-serif; padding: 24px;\">
            <h1>{request.law_firm_name}</h1>
            <h2>Invoice {request.invoice_number}</h2>
            <p><strong>Client:</strong> {request.client_name}</p>
            <p><strong>Matter:</strong> {request.matter_title}</p>
            <p><strong>Signed document delivered:</strong> {request.signed_document_name}</p>
            <p><strong>Issue date:</strong> {request.issue_date.isoformat()}</p>
            <p><strong>Due date:</strong> {request.due_date.isoformat()}</p>
            <p><strong>Follow-up date:</strong> {follow_up_iso}</p>
            <table width=\"100%\" cellspacing=\"0\" cellpadding=\"8\" border=\"1\" style=\"border-collapse: collapse;\">
              <thead>
                <tr><th>Description</th><th>Qty</th><th>Unit price</th><th>Line total</th></tr>
              </thead>
              <tbody>{lines_html}</tbody>
            </table>
            <p style=\"margin-top: 16px;\"><strong>Total:</strong> {request.currency} {total:.2f}</p>
          </body>
        </html>
        """.strip()

    def _build_email_html(self, request: MatterIntakeRequest, total: Decimal) -> str:
        return f"""
        <p>Hello {request.client_name},</p>
        <p>Your signed document for <strong>{request.matter_title}</strong> has been delivered, and the invoice is attached.</p>
        <p>Amount due: <strong>{request.currency} {total:.2f}</strong></p>
        <p>Invoice number: <strong>{request.invoice_number}</strong></p>
        <p>Thanks,<br>{request.law_firm_name}</p>
        """.strip()
