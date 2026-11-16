"""Dashboard aggregates — every number is computed from the database."""
import calendar
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import Appliance, Expense, MaintenanceRecord, MaintenanceSchedule, Notification, ReportedIssue, User
from app.services.notification_service import generate_alerts
from app.services.serializers import schedule_out
from app.utils.time import to_utc_iso

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
ACTIVE = ["Pending", "Scheduled", "In Progress"]


@router.get("/summary")
def summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    generate_alerts(db, user)
    today = date.today()
    now = datetime.now()
    appliances = db.scalars(select(Appliance).where(Appliance.user_id == user.id)).all()

    needs_maintenance = [a for a in appliances if a.risk_level in ("High", "Critical")
                         or (a.next_service_date and a.next_service_date <= today + timedelta(days=14))]
    upcoming_count = db.scalar(select(func.count(MaintenanceSchedule.id)).where(
        MaintenanceSchedule.user_id == user.id, MaintenanceSchedule.status.in_(ACTIVE),
        MaintenanceSchedule.scheduled_at >= now)) or 0
    overdue_count = db.scalar(select(func.count(MaintenanceSchedule.id)).where(
        MaintenanceSchedule.user_id == user.id, MaintenanceSchedule.status.in_(ACTIVE),
        MaintenanceSchedule.scheduled_at < now)) or 0
    completed_count = db.scalar(select(func.count(MaintenanceSchedule.id)).where(
        MaintenanceSchedule.user_id == user.id, MaintenanceSchedule.status == "Completed")) or 0
    total_expenses = float(db.scalar(select(func.coalesce(func.sum(Expense.amount), 0))
                                     .where(Expense.user_id == user.id)) or 0)
    open_issues = db.scalar(select(func.count(ReportedIssue.id)).where(
        ReportedIssue.user_id == user.id, ReportedIssue.status != "Resolved")) or 0

    # Health distribution
    dist = {k: 0 for k in ["Low", "Medium", "High", "Critical"]}
    for a in appliances:
        if a.risk_level in dist:
            dist[a.risk_level] += 1
    scored = [a.health_score for a in appliances if a.health_score is not None]
    avg_health = round(sum(scored) / len(scored), 1) if scored else None

    # Monthly expenses — last 12 months
    first = (today.replace(day=1) - timedelta(days=330)).replace(day=1)
    exp = db.scalars(select(Expense).where(Expense.user_id == user.id, Expense.expense_date >= first)).all()
    months = []
    y, m = first.year, first.month
    for _ in range(12):
        months.append({"key": f"{y}-{m:02d}", "label": f"{calendar.month_abbr[m]} {str(y)[2:]}", "total": 0.0})
        m += 1
        if m > 12:
            y, m = y + 1, 1
    idx = {mm["key"]: mm for mm in months}
    for e in exp:
        k = f"{e.expense_date.year}-{e.expense_date.month:02d}"
        if k in idx:
            idx[k]["total"] = round(idx[k]["total"] + float(e.amount), 2)

    # Upcoming calendar (next 60 days + overdue)
    cal = db.scalars(select(MaintenanceSchedule).where(
        MaintenanceSchedule.user_id == user.id, MaintenanceSchedule.status.in_(ACTIVE),
        MaintenanceSchedule.scheduled_at <= now + timedelta(days=60)
    ).order_by(MaintenanceSchedule.scheduled_at)).all()

    # Recent activities (merged feed)
    acts = []
    for r in db.scalars(select(MaintenanceRecord).where(MaintenanceRecord.user_id == user.id)
                        .order_by(MaintenanceRecord.created_at.desc()).limit(6)).all():
        acts.append({"type": "maintenance", "title": f"{r.maintenance_type} completed — {r.appliance.name}",
                     "at": r.created_at, "link": f"/appliances/{r.appliance_id}"})
    for i in db.scalars(select(ReportedIssue).where(ReportedIssue.user_id == user.id)
                        .order_by(ReportedIssue.created_at.desc()).limit(6)).all():
        acts.append({"type": "issue", "title": f"Issue reported: {i.problem_category} — {i.appliance.name} ({i.severity})",
                     "at": i.created_at, "link": "/issues"})
    for e in db.scalars(select(Expense).where(Expense.user_id == user.id)
                        .order_by(Expense.created_at.desc()).limit(6)).all():
        acts.append({"type": "expense", "title": f"Expense ₹{float(e.amount):,.0f} — {e.expense_type}"
                     + (f" ({e.appliance.name})" if e.appliance else ""), "at": e.created_at, "link": "/expenses"})
    for s in db.scalars(select(MaintenanceSchedule).where(MaintenanceSchedule.user_id == user.id)
                        .order_by(MaintenanceSchedule.created_at.desc()).limit(6)).all():
        acts.append({"type": "schedule", "title": f"Task {s.status.lower()}: {s.title}",
                     "at": s.updated_at, "link": "/scheduler"})
    for a in db.scalars(select(Appliance).where(Appliance.user_id == user.id)
                        .order_by(Appliance.created_at.desc()).limit(4)).all():
        acts.append({"type": "appliance", "title": f"Appliance added: {a.name}", "at": a.created_at,
                     "link": f"/appliances/{a.id}"})
    acts.sort(key=lambda x: x["at"], reverse=True)
    for x in acts:
        x["at"] = to_utc_iso(x["at"])

    alerts = db.scalars(select(Notification).where(
        Notification.user_id == user.id, Notification.is_read.is_(False),
        Notification.type.in_(["high_risk", "critical_issue", "warranty", "pending_maintenance"])
    ).order_by(Notification.created_at.desc()).limit(6)).all()

    return {
        "stats": {
            "total_appliances": len(appliances),
            "needs_maintenance": len(needs_maintenance),
            "upcoming_tasks": upcoming_count,
            "overdue_tasks": overdue_count,
            "completed_tasks": completed_count,
            "total_expenses": round(total_expenses, 2),
            "open_issues": open_issues,
            "average_health": avg_health,
        },
        "health_distribution": [{"risk": k, "count": v} for k, v in dist.items()],
        "appliance_health": sorted(
            [{"id": a.id, "name": a.name, "category": a.category, "health_score": a.health_score,
              "risk_level": a.risk_level, "next_service_date": a.next_service_date} for a in appliances],
            key=lambda x: x["health_score"] if x["health_score"] is not None else 101),
        "monthly_expenses": [{"month": mm["label"], "total": mm["total"]} for mm in months],
        "calendar": [schedule_out(s).model_dump() for s in cal],
        "recent_activities": acts[:10],
        "alerts": [{"id": n.id, "type": n.type, "severity": n.severity, "title": n.title, "message": n.message,
                    "link": n.link, "created_at": to_utc_iso(n.created_at)} for n in alerts],
    }
