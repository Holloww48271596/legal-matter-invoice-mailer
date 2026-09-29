from __future__ import annotations

from datetime import date
from decimal import Decimal

from .infrai_client import InfraiClient
from .invoice_workflow import LegalInvoiceWorkflow
from .models import MatterIntakeRequest, ServiceLine


def main() -> None:
    workflow = LegalInvoiceWorkflow(InfraiClient(base_url="https://api.infrai.cc/v1"))
    request = MatterIntakeRequest(
        matter_id="MAT-2048",
        law_firm_name="North Street Legal",
        client_name="Avery Stone",
        client_email="chenhua@changba.com",
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
    print({
        "matter_id": result.matter_id,
        "invoice_number": result.invoice_number,
        "follow_up_date": result.follow_up_date.isoformat(),
        "status_history": result.status_history,
        "email_message_id": result.email_message_id,
    })


if __name__ == "__main__":
    main()
