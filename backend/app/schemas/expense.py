from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import EXPENSE_TYPES
from app.utils.time import UTCDateTime
from app.schemas.common import ORMModel, choice, optional_choice


class ExpenseCreate(BaseModel):
    appliance_id: int | None = None
    expense_type: choice(EXPENSE_TYPES, "expense_type")
    amount: float = Field(gt=0, le=10_000_000)
    expense_date: date
    vendor: str | None = Field(default=None, max_length=120)
    description: str | None = None


class ExpenseUpdate(BaseModel):
    appliance_id: int | None = None
    expense_type: optional_choice(EXPENSE_TYPES, "expense_type") = None
    amount: float | None = Field(default=None, gt=0, le=10_000_000)
    expense_date: date | None = None
    vendor: str | None = None
    description: str | None = None


class ExpenseOut(ORMModel):
    id: int
    appliance_id: int | None
    appliance_name: str | None = None
    expense_type: str
    amount: float
    expense_date: date
    vendor: str | None
    description: str | None
    created_at: UTCDateTime


class ExpenseSummary(BaseModel):
    year: int
    total_all_time: float
    total_year: float
    monthly: list[dict]  # [{month: "Jan", total: 0.0, Repair: .., Servicing: ..}]
    yearly: list[dict]  # [{year: 2025, total: ...}]
    by_appliance: list[dict]  # [{appliance_id, appliance_name, total}]
    by_type: list[dict]
    highest_cost_appliance: dict | None
