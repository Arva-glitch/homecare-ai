"""Runs predictions for appliances, persists PredictionHistory and updates cached risk fields."""
import json
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.features import extract_features
from app.ml.predictor import predictor
from app.models import Appliance, MaintenanceSchedule, PredictionHistory


def predict_appliance(db: Session, appliance: Appliance, commit: bool = True) -> PredictionHistory:
    db.refresh(appliance)  # make sure records/issues relationships are current
    f = extract_features(appliance)
    last_service = appliance.last_service_date
    if appliance.maintenance_records:
        latest = max(r.service_date for r in appliance.maintenance_records)
        last_service = max(filter(None, [last_service, latest]))
    result = predictor.predict(f, appliance.category, last_service)

    record = PredictionHistory(
        user_id=appliance.user_id,
        appliance_id=appliance.id,
        health_score=result.health_score,
        risk_level=result.risk_level,
        priority=result.priority,
        recommended_service_date=result.recommended_service_date,
        model_used=result.model_used,
        confidence=result.confidence,
        explanation=json.dumps({
            "lines": result.explanation,
            "factors": result.factors,
            "probabilities": result.class_probabilities,
        }),
        features=json.dumps(result.features),
    )
    db.add(record)
    appliance.health_score = result.health_score
    appliance.risk_level = result.risk_level
    appliance.next_service_date = result.recommended_service_date
    if commit:
        db.commit()
        db.refresh(record)
    else:
        db.flush()
    return record


def predict_all(db: Session, user_id: int) -> list[PredictionHistory]:
    appliances = db.scalars(select(Appliance).where(Appliance.user_id == user_id)).all()
    results = [predict_appliance(db, a, commit=False) for a in appliances]
    db.commit()
    for r in results:
        db.refresh(r)
    return results


MAINT_TYPE_BY_CATEGORY = {
    "Air Conditioner": "General Servicing",
    "Water Purifier": "Filter Change",
    "Refrigerator": "General Servicing",
    "Washing Machine": "Cleaning",
    "Geyser": "Inspection",
}


def suggestion_for(appliance: Appliance, reason_prefix: str = "") -> dict:
    risk = appliance.risk_level or "Low"
    priority = {"Critical": "Urgent", "High": "High", "Medium": "Normal"}.get(risk, "Low")
    mtype = "Repair" if risk == "Critical" else MAINT_TYPE_BY_CATEGORY.get(appliance.category, "Inspection")
    when = appliance.next_service_date or date.today()
    reason = reason_prefix or (
        f"Health score {appliance.health_score:.0f}/100 ({risk} risk). "
        f"Recommended service by {when.strftime('%d %b %Y')}."
    )
    return {
        "appliance_id": appliance.id,
        "appliance_name": appliance.name,
        "category": appliance.category,
        "risk_level": risk,
        "health_score": appliance.health_score or 0,
        "suggested_date": when,
        "maintenance_type": mtype,
        "priority": priority,
        "reason": reason,
    }


def schedule_suggestions(db: Session, user_id: int, horizon_days: int = 45) -> list[dict]:
    """AI-suggested schedules: appliances at Medium+ risk or due within the horizon, with no active task."""
    appliances = db.scalars(select(Appliance).where(Appliance.user_id == user_id)).all()
    active = set(db.scalars(
        select(MaintenanceSchedule.appliance_id).where(
            MaintenanceSchedule.user_id == user_id,
            MaintenanceSchedule.status.in_(["Pending", "Scheduled", "In Progress"]),
        )
    ).all())
    today = date.today()
    out = []
    for a in appliances:
        if a.id in active or a.health_score is None:
            continue
        due_soon = a.next_service_date and (a.next_service_date - today).days <= horizon_days
        if a.risk_level in ("Medium", "High", "Critical") or due_soon:
            out.append(suggestion_for(a))
    order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    out.sort(key=lambda s: (order.get(s["risk_level"], 4), s["suggested_date"]))
    return out
