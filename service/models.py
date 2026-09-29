from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class ServiceLine(BaseModel):
    description: str
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(gt=0)


class MatterIntakeRequest(BaseModel):
    matter_id: str
    law_firm_name: str
    client_name: str
    client_email: EmailStr
    matter_title: str
    services: list[ServiceLine]
    currency: Literal["USD", "EUR", "GBP"] = "USD"
    invoice_number: str
    issue_date: date
    due_date: date
    signed_document_name: str


class WorkflowResult(BaseModel):
    matter_id: str
    invoice_number: str
    total_amount: str
    currency: str
    follow_up_date: date
    status_history: list[str]
    pdf_bytes: bytes
    email_message_id: str
