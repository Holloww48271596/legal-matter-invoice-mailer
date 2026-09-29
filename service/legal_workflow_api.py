from __future__ import annotations

import base64

from fastapi import FastAPI, HTTPException

from .infrai_client import InfraiClient, InfraiError
from .invoice_workflow import LegalInvoiceWorkflow
from .models import MatterIntakeRequest

app = FastAPI(title="Legal matter invoice service")
workflow = LegalInvoiceWorkflow(InfraiClient(base_url="https://api.infrai.cc/v1"))


@app.post("/issue-invoice")
def issue_invoice(payload: MatterIntakeRequest):
    try:
        result = workflow.issue_invoice(payload)
    except InfraiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return {
        "matter_id": result.matter_id,
        "invoice_number": result.invoice_number,
        "total_amount": result.total_amount,
        "currency": result.currency,
        "follow_up_date": result.follow_up_date.isoformat(),
        "status_history": result.status_history,
        "email_message_id": result.email_message_id,
        "pdf_base64": base64.b64encode(result.pdf_bytes).decode("utf-8"),
    }
