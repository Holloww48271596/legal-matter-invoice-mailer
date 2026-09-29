from __future__ import annotations

import base64
from datetime import date
from decimal import Decimal

from service.invoice_workflow import LegalInvoiceWorkflow
from service.models import MatterIntakeRequest, ServiceLine


class StubInfraiClient:
    def pdf_generate(self, *, html: str, page_size: str = "A4", orientation: str = "portrait", store: bool = False):
        assert "Invoice INV-2048" in html
        return {
            "ok": True,
            "data": {
                "pdf_base64": base64.b64encode(b"pdf-bytes").decode("utf-8")
            },
            "error": None,
            "metadata": {},
        }

    def email_send(self, *, to: str, subject: str, html: str, attachments=None):
        assert to == "avery@example.com"
        assert subject == "Invoice INV-2048 for Fixed-fee contract review"
        assert attachments[0]["filename"] == "INV-2048.pdf"
        return {
            "ok": True,
            "data": {
                "message_id": "msg_123"
            },
            "error": None,
            "metadata": {},
        }

    @staticmethod
    def as_base64(data: bytes) -> str:
        return base64.b64encode(data).decode("utf-8")


def test_issue_invoice_sets_short_deadline_follow_up_and_statuses():
    workflow = LegalInvoiceWorkflow(StubInfraiClient())
    request = MatterIntakeRequest(
        matter_id="MAT-2048",
        law_firm_name="North Street Legal",
        client_name="Avery Stone",
        client_email="avery@example.com",
        matter_title="Fixed-fee contract review",
        services=[
            ServiceLine(description="Contract review", quantity=Decimal("1"), unit_price=Decimal("900.00")),
            ServiceLine(description="Redline summary", quantity=Decimal("1"), unit_price=Decimal("250.00")),
        ],
        currency="USD",
        invoice_number="INV-2048",
        issue_date=date(2026, 5, 6),
        due_date=date(2026, 5, 20),
        signed_document_name="signed-engagement-letter.pdf",
    )

    result = workflow.issue_invoice(request)

    assert result.follow_up_date == date(2026, 5, 17)
    assert result.total_amount == "1150.00"
    assert result.status_history == [
        "intake_recorded",
        "invoice_issued",
        "signed_document_sent",
        "deadline_followup_scheduled",
    ]
    assert result.email_message_id == "msg_123"
    assert result.pdf_bytes == b"pdf-bytes"
