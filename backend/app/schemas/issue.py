from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import ISSUE_STATUSES, PROBLEM_CATEGORIES, SEVERITIES
from app.utils.time import UTCDateTime
from app.schemas.common import ORMModel, choice, optional_choice
from app.schemas.prediction import PredictionOut


class IssueCreate(BaseModel):
    appliance_id: int
    problem_category: choice(PROBLEM_CATEGORIES, "problem_category")
    description: str = Field(min_length=5, max_length=4000)
    severity: choice(SEVERITIES, "severity")
    reported_date: date | None = None


class IssueUpdate(BaseModel):
    problem_category: optional_choice(PROBLEM_CATEGORIES, "problem_category") = None
    description: str | None = Field(default=None, min_length=5, max_length=4000)
    severity: optional_choice(SEVERITIES, "severity") = None
    status: optional_choice(ISSUE_STATUSES, "status") = None


class IssueOut(ORMModel):
    id: int
    appliance_id: int
    appliance_name: str | None = None
    appliance_category: str | None = None
    problem_category: str
    description: str
    severity: str
    priority: str
    status: str
    reported_date: date
    image_url: str | None = None
    ai_suggestions: str | None
    suggestion_source: str | None
    resolved_at: UTCDateTime | None
    created_at: UTCDateTime


class RecommendedSchedule(BaseModel):
    appliance_id: int
    suggested_date: date
    maintenance_type: str
    priority: str
    reason: str


class IssueCreateResponse(BaseModel):
    issue: IssueOut
    prediction: PredictionOut
    recommended_schedule: RecommendedSchedule | None
