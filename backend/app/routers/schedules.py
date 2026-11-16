from typing import Literal
from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.utils.time import utcnow
from app.core.deps import get_current_user, get_owned_appliance
from app.db.session import get_db
from app.models import Expense, MaintenanceRecord, MaintenanceSchedule, User
from app.schemas.common import Message
from app.schemas.maintenance import ScheduleCreate, ScheduleOut, ScheduleSuggestion, ScheduleUpdate, StatusUpdate
from app.services.notification_service import generate_alerts
from app.services.prediction_service import predict_appliance, schedule_suggestions
from app.services.serializers import schedule_out

router = APIRouter(prefix="/schedules", tags=["Maintenance Scheduler"])

ACTIVE = ["Pending", "Scheduled", "In Progress"]
# Allowed status transitions
TRANSITIONS = {
    "Pending": {"Scheduled", "In Progress", "Completed", "Cancelled"},
    "Scheduled": {"Pending", "In Progress", "Completed", "Cancelled"},
    "In Progress": {"Scheduled", "Completed", "Cancelled"},
    "Completed": set(),
    "Cancelled": {"Pending", "Scheduled"},
}


def _get(db: Session, user: User, schedule_id: int) -> MaintenanceSchedule:
    s = db.get(MaintenanceSchedule, schedule_id)
    if not s or s.user_id != user.id:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return s


@router.get("", response_model=list[ScheduleOut])
def list_schedules(
    view: Literal["all", "upcoming", "completed", "cancelled", "overdue"] = "all",
    status_filter: str | None = Query(None, alias="status"),
    appliance_id: int | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = select(MaintenanceSchedule).where(MaintenanceSchedule.user_id == user.id)
    now = datetime.now()
    if view == "upcoming":
        q = q.where(MaintenanceSchedule.status.in_(ACTIVE), MaintenanceSchedule.scheduled_at >= now)
    elif view == "overdue":
        q = q.where(MaintenanceSchedule.status.in_(ACTIVE), MaintenanceSchedule.scheduled_at < now)
    elif view == "completed":
        q = q.where(MaintenanceSchedule.status == "Completed")
    elif view == "cancelled":
        q = q.where(MaintenanceSchedule.status == "Cancelled")
    if status_filter:
        q = q.where(MaintenanceSchedule.status == status_filter)
    if appliance_id:
        q = q.where(MaintenanceSchedule.appliance_id == appliance_id)
    if start:
        q = q.where(MaintenanceSchedule.scheduled_at >= start)
    if end:
        q = q.where(MaintenanceSchedule.scheduled_at <= end)
    desc_order = view in ("completed", "cancelled")
    q = q.order_by(MaintenanceSchedule.scheduled_at.desc() if desc_order else MaintenanceSchedule.scheduled_at)
    return [schedule_out(s) for s in db.scalars(q).all()]


@router.post("", response_model=ScheduleOut, status_code=status.HTTP_201_CREATED)
def create_schedule(payload: ScheduleCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = get_owned_appliance(db, user, payload.appliance_id)
    data = payload.model_dump()
    data["title"] = (data.get("title") or f"{payload.maintenance_type} – {a.name}")[:160]
    s = MaintenanceSchedule(user_id=user.id, **data)
    db.add(s)
    db.commit()
    db.refresh(s)
    generate_alerts(db, user)
    return schedule_out(s)


@router.get("/suggestions", response_model=list[ScheduleSuggestion])
def suggestions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Schedules automatically suggested from the latest predictive analysis."""
    return schedule_suggestions(db, user.id)


class AcceptSuggestion(BaseModel):
    appliance_id: int
    scheduled_at: datetime | None = None


@router.post("/suggestions/accept", response_model=ScheduleOut, status_code=201)
def accept_suggestion(payload: AcceptSuggestion, user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    a = get_owned_appliance(db, user, payload.appliance_id)
    from app.services.prediction_service import suggestion_for

    sug = suggestion_for(a)
    when = payload.scheduled_at or datetime.combine(sug["suggested_date"], time(10, 0))
    s = MaintenanceSchedule(
        user_id=user.id, appliance_id=a.id, title=f"{sug['maintenance_type']} – {a.name}",
        maintenance_type=sug["maintenance_type"], scheduled_at=when, status="Pending",
        priority=sug["priority"], description=f"AI-suggested: {sug['reason']}", is_ai_suggested=True,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    generate_alerts(db, user)
    return schedule_out(s)


@router.get("/{schedule_id}", response_model=ScheduleOut)
def get_schedule(schedule_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return schedule_out(_get(db, user, schedule_id))


@router.put("/{schedule_id}", response_model=ScheduleOut)
def update_schedule(schedule_id: int, payload: ScheduleUpdate, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    s = _get(db, user, schedule_id)
    if s.status in ("Completed", "Cancelled"):
        raise HTTPException(status_code=400, detail=f"Cannot edit a {s.status.lower()} task")
    changes = payload.model_dump(exclude_unset=True)
    if "appliance_id" in changes and changes["appliance_id"] is not None:
        get_owned_appliance(db, user, changes["appliance_id"])
    for k, v in changes.items():
        if v is not None or k in ("description", "technician", "estimated_cost"):
            setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return schedule_out(s)


@router.patch("/{schedule_id}/status", response_model=ScheduleOut)
def update_status(schedule_id: int, payload: StatusUpdate, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    s = _get(db, user, schedule_id)
    new = payload.status
    if new == s.status:
        return schedule_out(s)
    if new not in TRANSITIONS[s.status]:
        raise HTTPException(status_code=400, detail=f"Cannot change status from {s.status} to {new}")
    s.status = new
    if new == "Completed":
        s.completed_at = utcnow()
        a = s.appliance
        service_date = date.today()
        cost = payload.actual_cost if payload.actual_cost is not None else float(s.estimated_cost or 0)
        db.add(MaintenanceRecord(
            user_id=user.id, appliance_id=a.id, schedule_id=s.id, service_date=service_date,
            maintenance_type=s.maintenance_type, description=payload.notes or s.description,
            technician=s.technician, cost=cost, was_breakdown=payload.was_breakdown,
        ))
        if not a.last_service_date or service_date > a.last_service_date:
            a.last_service_date = service_date
        if cost and cost > 0:
            etype = "Repair" if s.maintenance_type == "Repair" or payload.was_breakdown else (
                "Parts" if s.maintenance_type in ("Part Replacement", "Filter Change") else "Servicing")
            db.add(Expense(user_id=user.id, appliance_id=a.id, expense_type=etype, amount=cost,
                           expense_date=service_date, vendor=s.technician, description=s.title))
        # Resolve open issues of this appliance when a repair is completed
        if s.maintenance_type == "Repair":
            for i in a.issues:
                if i.status != "Resolved":
                    i.status = "Resolved"
                    i.resolved_at = utcnow()
        db.commit()
        predict_appliance(db, a)
    else:
        db.commit()
    db.refresh(s)
    generate_alerts(db, user)
    return schedule_out(s)


@router.post("/{schedule_id}/cancel", response_model=ScheduleOut)
def cancel_schedule(schedule_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = _get(db, user, schedule_id)
    if s.status in ("Completed", "Cancelled"):
        raise HTTPException(status_code=400, detail=f"Task is already {s.status.lower()}")
    s.status = "Cancelled"
    db.commit()
    db.refresh(s)
    return schedule_out(s)


@router.delete("/{schedule_id}", response_model=Message)
def delete_schedule(schedule_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = _get(db, user, schedule_id)
    db.delete(s)
    db.commit()
    return Message(message="Schedule deleted")
