"""Generates in-app alerts (idempotent via dedupe keys) and optionally emails critical ones."""
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Appliance, MaintenanceSchedule, Notification, ReportedIssue, User
from app.utils.email import send_email


def _create(db: Session, user: User, *, type: str, severity: str, title: str, message: str,
            link: str | None, key: str) -> Notification | None:
    exists = db.scalar(select(Notification.id).where(Notification.user_id == user.id,
                                                     Notification.dedupe_key == key))
    if exists:
        return None
    n = Notification(user_id=user.id, type=type, severity=severity, title=title, message=message,
                     link=link, dedupe_key=key)
    db.add(n)
    db.flush()
    if severity == "danger" and user.email_notifications:
        n.emailed = send_email(user.email, f"[HomeCare AI] {title}", message)
    return n


def notify(db: Session, user: User, *, type: str, severity: str, title: str, message: str,
           link: str | None = None, key: str | None = None) -> Notification | None:
    key = key or f"{type}:{datetime.now().isoformat()}"
    n = _create(db, user, type=type, severity=severity, title=title, message=message, link=link, key=key)
    db.commit()
    return n


def generate_alerts(db: Session, user: User) -> int:
    """Scan the user's data and create any missing alerts. Returns how many were created."""
    today = date.today()
    now = datetime.now()
    created = 0

    appliances = db.scalars(select(Appliance).where(Appliance.user_id == user.id)).all()
    for a in appliances:
        # Warranty expiration (within 30 days, or expired within the last 7 days)
        if a.warranty_expiry:
            days = (a.warranty_expiry - today).days
            if 0 <= days <= 30:
                created += bool(_create(
                    db, user, type="warranty", severity="warning",
                    title=f"Warranty expiring: {a.name}",
                    message=f"The warranty for {a.name} expires on {a.warranty_expiry:%d %b %Y} ({days} days). "
                            "Consider a check-up while it is still covered.",
                    link=f"/appliances/{a.id}", key=f"warranty:{a.id}:{a.warranty_expiry}"))
            elif -7 <= days < 0:
                created += bool(_create(
                    db, user, type="warranty", severity="info",
                    title=f"Warranty expired: {a.name}",
                    message=f"The warranty for {a.name} expired on {a.warranty_expiry:%d %b %Y}.",
                    link=f"/appliances/{a.id}", key=f"warranty-expired:{a.id}:{a.warranty_expiry}"))
        # High-risk appliances (one alert per appliance per risk level per week)
        if a.risk_level in ("High", "Critical"):
            week = today.isocalendar()
            created += bool(_create(
                db, user, type="high_risk", severity="danger" if a.risk_level == "Critical" else "warning",
                title=f"{a.risk_level} risk: {a.name}",
                message=f"{a.name} has a health score of {a.health_score:.0f}/100. "
                        f"Recommended servicing by {a.next_service_date:%d %b %Y}." if a.next_service_date else
                        f"{a.name} has a health score of {a.health_score:.0f}/100.",
                link="/predictions", key=f"risk:{a.id}:{a.risk_level}:{week[0]}-{week[1]}"))

    schedules = db.scalars(select(MaintenanceSchedule).where(
        MaintenanceSchedule.user_id == user.id,
        MaintenanceSchedule.status.in_(["Pending", "Scheduled", "In Progress"]))).all()
    for s in schedules:
        delta = s.scheduled_at - now
        if timedelta(0) <= delta <= timedelta(days=7):
            created += bool(_create(
                db, user, type="upcoming_service", severity="info",
                title=f"Upcoming: {s.title}",
                message=f"{s.title} for {s.appliance.name} is scheduled on {s.scheduled_at:%d %b %Y, %I:%M %p}.",
                link="/scheduler", key=f"upcoming:{s.id}:{s.scheduled_at:%Y%m%d%H%M}"))
        elif delta < timedelta(0):
            created += bool(_create(
                db, user, type="pending_maintenance", severity="warning",
                title=f"Overdue maintenance: {s.title}",
                message=f"{s.title} for {s.appliance.name} was due on {s.scheduled_at:%d %b %Y} and is still "
                        f"'{s.status}'. Update its status or reschedule.",
                link="/scheduler", key=f"overdue:{s.id}:{s.scheduled_at:%Y%m%d%H%M}"))
        elif s.status == "Pending":
            created += bool(_create(
                db, user, type="pending_maintenance", severity="info",
                title=f"Pending confirmation: {s.title}",
                message=f"{s.title} for {s.appliance.name} is pending. Confirm a technician and mark it Scheduled.",
                link="/scheduler", key=f"pending:{s.id}"))

    issues = db.scalars(select(ReportedIssue).where(
        ReportedIssue.user_id == user.id, ReportedIssue.severity == "Critical",
        ReportedIssue.status != "Resolved")).all()
    for i in issues:
        created += bool(_create(
            db, user, type="critical_issue", severity="danger",
            title=f"Critical issue: {i.appliance.name}",
            message=f"{i.problem_category} reported on {i.reported_date:%d %b %Y}: {i.description[:140]}",
            link="/issues", key=f"critical-issue:{i.id}"))

    db.commit()
    return created
