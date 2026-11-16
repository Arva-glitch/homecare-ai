"""Convert ORM objects into response schemas (adds computed / joined fields)."""
import json

from app.schemas.appliance import ApplianceOut
from app.schemas.expense import ExpenseOut
from app.schemas.issue import IssueOut
from app.schemas.maintenance import ScheduleOut
from app.schemas.prediction import PredictionOut
from app.utils.files import upload_url


def appliance_out(a) -> ApplianceOut:
    out = ApplianceOut.model_validate(a)
    out.image_url = upload_url(a.image_path)
    return out


def schedule_out(s) -> ScheduleOut:
    out = ScheduleOut.model_validate(s)
    if s.appliance:
        out.appliance_name = s.appliance.name
        out.appliance_category = s.appliance.category
    return out


def issue_out(i) -> IssueOut:
    out = IssueOut.model_validate(i)
    out.image_url = upload_url(i.image_path)
    if i.appliance:
        out.appliance_name = i.appliance.name
        out.appliance_category = i.appliance.category
    return out


def expense_out(e) -> ExpenseOut:
    out = ExpenseOut.model_validate(e)
    out.appliance_name = e.appliance.name if e.appliance else None
    return out


def prediction_out(p, factors=None, probs=None) -> PredictionOut:
    data = {
        "id": p.id,
        "appliance_id": p.appliance_id,
        "appliance_name": p.appliance.name if p.appliance else None,
        "appliance_category": p.appliance.category if p.appliance else None,
        "health_score": p.health_score,
        "risk_level": p.risk_level,
        "priority": p.priority,
        "recommended_service_date": p.recommended_service_date,
        "model_used": p.model_used,
        "confidence": p.confidence,
        "created_at": p.created_at,
    }
    stored = json.loads(p.explanation) if p.explanation else {}
    if isinstance(stored, list):  # legacy format
        stored = {"lines": stored}
    data["explanation"] = stored.get("lines", [])
    data["factors"] = factors if factors is not None else stored.get("factors", [])
    data["class_probabilities"] = probs if probs is not None else stored.get("probabilities")
    return PredictionOut(**data)
