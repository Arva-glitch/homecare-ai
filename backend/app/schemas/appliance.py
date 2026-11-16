from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.models.enums import (
    APPLIANCE_CATEGORIES,
    CONDITIONS,
    MAINTENANCE_TYPES,
    USAGE_FREQUENCIES,
)
from app.utils.time import UTCDateTime
from app.schemas.common import ORMModel, choice, optional_choice


class ApplianceBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: choice(APPLIANCE_CATEGORIES, "category")
    brand: str | None = Field(default=None, max_length=80)
    model_number: str | None = Field(default=None, max_length=80)
    purchase_date: date | None = None
    installation_date: date | None = None
    warranty_expiry: date | None = None
    expected_lifespan_years: float | None = Field(default=None, gt=0, le=50)
    last_service_date: date | None = None
    usage_frequency: choice(USAGE_FREQUENCIES, "usage_frequency") = "Medium"
    condition: choice(CONDITIONS, "condition") = "Good"
    location: str | None = Field(default=None, max_length=80)
    notes: str | None = None

    @model_validator(mode="after")
    def _dates(self):
        today = date.today()
        if self.purchase_date and self.purchase_date > today:
            raise ValueError("purchase_date cannot be in the future")
        if self.last_service_date and self.last_service_date > today:
            raise ValueError("last_service_date cannot be in the future")
        if self.purchase_date and self.installation_date and self.installation_date < self.purchase_date:
            raise ValueError("installation_date cannot be before purchase_date")
        return self


class ApplianceCreate(ApplianceBase):
    pass


class ApplianceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    category: optional_choice(APPLIANCE_CATEGORIES, "category") = None
    brand: str | None = None
    model_number: str | None = None
    purchase_date: date | None = None
    installation_date: date | None = None
    warranty_expiry: date | None = None
    expected_lifespan_years: float | None = Field(default=None, gt=0, le=50)
    last_service_date: date | None = None
    usage_frequency: optional_choice(USAGE_FREQUENCIES, "usage_frequency") = None
    condition: optional_choice(CONDITIONS, "condition") = None
    location: str | None = None
    notes: str | None = None


class ApplianceOut(ORMModel):
    id: int
    name: str
    category: str
    brand: str | None
    model_number: str | None
    purchase_date: date | None
    installation_date: date | None
    warranty_expiry: date | None
    expected_lifespan_years: float
    last_service_date: date | None
    usage_frequency: str
    condition: str
    location: str | None
    notes: str | None
    image_url: str | None = None
    health_score: float | None
    risk_level: str | None
    next_service_date: date | None
    created_at: UTCDateTime
    updated_at: UTCDateTime


class MaintenanceRecordCreate(BaseModel):
    service_date: date
    maintenance_type: choice(MAINTENANCE_TYPES, "maintenance_type")
    description: str | None = None
    technician: str | None = Field(default=None, max_length=120)
    cost: float = Field(default=0, ge=0)
    was_breakdown: bool = False
    add_expense: bool = True

    @model_validator(mode="after")
    def _d(self):
        if self.service_date > date.today():
            raise ValueError("service_date cannot be in the future")
        return self


class MaintenanceRecordOut(ORMModel):
    id: int
    appliance_id: int
    schedule_id: int | None
    service_date: date
    maintenance_type: str
    description: str | None
    technician: str | None
    cost: float
    was_breakdown: bool
    created_at: UTCDateTime


class ApplianceDetail(ApplianceOut):
    maintenance_records: list[MaintenanceRecordOut] = []
    open_issues: int = 0
    total_expenses: float = 0
    warranty_active: bool | None = None
    age_years: float | None = None


class ApplianceList(BaseModel):
    items: list[ApplianceOut]
    total: int
