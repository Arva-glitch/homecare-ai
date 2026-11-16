from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import MAINTENANCE_TYPES, SCHEDULE_STATUSES
from app.utils.time import UTCDateTime
from app.schemas.common import ORMModel, choice, optional_choice


class ScheduleCreate(BaseModel):
    appliance_id: int
    title: str | None = Field(default=None, max_length=160)
    maintenance_type: choice(MAINTENANCE_TYPES, "maintenance_type")
    scheduled_at: datetime
    description: str | None = None
    status: choice(["Pending", "Scheduled"], "status") = "Scheduled"
    priority: choice(["Low", "Normal", "High", "Urgent"], "priority") = "Normal"
    technician: str | None = Field(default=None, max_length=120)
    estimated_cost: float | None = Field(default=None, ge=0)
    is_ai_suggested: bool = False


class ScheduleUpdate(BaseModel):
    appliance_id: int | None = None
    title: str | None = Field(default=None, max_length=160)
    maintenance_type: optional_choice(MAINTENANCE_TYPES, "maintenance_type") = None
    scheduled_at: datetime | None = None
    description: str | None = None
    priority: optional_choice(["Low", "Normal", "High", "Urgent"], "priority") = None
    technician: str | None = None
    estimated_cost: float | None = Field(default=None, ge=0)


class StatusUpdate(BaseModel):
    status: choice(SCHEDULE_STATUSES, "status")
    # Used when completing a task: records the actual cost and creates an expense.
    actual_cost: float | None = Field(default=None, ge=0)
    notes: str | None = None
    was_breakdown: bool = False


class ScheduleOut(ORMModel):
    id: int
    appliance_id: int
    appliance_name: str | None = None
    appliance_category: str | None = None
    title: str
    maintenance_type: str
    scheduled_at: datetime
    description: str | None
    status: str
    priority: str
    technician: str | None
    estimated_cost: float | None
    is_ai_suggested: bool
    completed_at: UTCDateTime | None
    created_at: UTCDateTime


class ScheduleSuggestion(BaseModel):
    appliance_id: int
    appliance_name: str
    category: str
    risk_level: str
    health_score: float
    suggested_date: date
    maintenance_type: str
    priority: str
    reason: str
