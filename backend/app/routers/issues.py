from datetime import date, datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.utils.time import utcnow
from app.core.deps import get_current_user, get_owned_appliance
from app.db.session import get_db
from app.models import ReportedIssue, User
from app.schemas.common import Message
from app.schemas.issue import IssueCreate, IssueCreateResponse, IssueOut, IssueUpdate, RecommendedSchedule
from app.services.chat_service import issue_suggestions
from app.services.notification_service import generate_alerts
from app.services.prediction_service import predict_appliance
from app.services.serializers import issue_out, prediction_out
from app.utils.files import delete_upload, save_image

router = APIRouter(prefix="/issues", tags=["Issue Reporting"])

SEVERITY_TO_P = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}


def compute_priority(severity: str, appliance_risk: str | None, warranty_active: bool) -> str:
    """P1 (most urgent) .. P4. Bumped one level when the appliance is already High/Critical risk."""
    p = SEVERITY_TO_P[severity]
    if appliance_risk in ("High", "Critical"):
        p -= 1
    return f"P{max(1, p)}"


def _get(db: Session, user: User, issue_id: int) -> ReportedIssue:
    i = db.get(ReportedIssue, issue_id)
    if not i or i.user_id != user.id:
        raise HTTPException(status_code=404, detail="Issue not found")
    return i


@router.get("", response_model=list[IssueOut])
def list_issues(status_filter: str | None = None, appliance_id: int | None = None,
                user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(ReportedIssue).where(ReportedIssue.user_id == user.id)
    if status_filter:
        q = q.where(ReportedIssue.status == status_filter)
    if appliance_id:
        q = q.where(ReportedIssue.appliance_id == appliance_id)
    q = q.order_by(ReportedIssue.reported_date.desc(), ReportedIssue.id.desc())
    return [issue_out(i) for i in db.scalars(q).all()]


@router.post("", response_model=IssueCreateResponse, status_code=status.HTTP_201_CREATED)
def report_issue(payload: IssueCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = get_owned_appliance(db, user, payload.appliance_id)
    reported = payload.reported_date or date.today()
    if reported > date.today():
        raise HTTPException(status_code=422, detail="reported_date cannot be in the future")
    warranty_active = bool(a.warranty_expiry and a.warranty_expiry >= date.today())
    text, source = issue_suggestions(a, payload.problem_category, payload.description, payload.severity)
    issue = ReportedIssue(
        user_id=user.id, appliance_id=a.id, problem_category=payload.problem_category,
        description=payload.description, severity=payload.severity,
        priority=compute_priority(payload.severity, a.risk_level, warranty_active),
        reported_date=reported, ai_suggestions=text, suggestion_source=source,
    )
    db.add(issue)
    if payload.severity in ("High", "Critical") and a.condition in ("Excellent", "Good"):
        a.condition = "Fair"
    db.commit()
    db.refresh(issue)

    # Update the appliance risk assessment with the new issue
    pred = predict_appliance(db, a)
    db.refresh(issue)
    # Priority may increase now that risk was re-assessed
    issue.priority = compute_priority(issue.severity, a.risk_level, warranty_active)
    db.commit()
    generate_alerts(db, user)

    rec = None
    if issue.severity in ("Medium", "High", "Critical") or a.risk_level in ("Medium", "High", "Critical"):
        rec = RecommendedSchedule(
            appliance_id=a.id, suggested_date=pred.recommended_service_date,
            maintenance_type="Repair" if issue.severity in ("High", "Critical") else "Inspection",
            priority={"P1": "Urgent", "P2": "High", "P3": "Normal"}.get(issue.priority, "Low"),
            reason=f"{issue.problem_category} reported ({issue.severity}). Updated health score "
                   f"{pred.health_score:.0f}/100 — {pred.risk_level} risk.",
        )
        if warranty_active:
            rec.reason += f" Appliance is under warranty until {a.warranty_expiry:%d %b %Y}."
    return IssueCreateResponse(issue=issue_out(issue), prediction=prediction_out(pred), recommended_schedule=rec)


@router.get("/{issue_id}", response_model=IssueOut)
def get_issue(issue_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return issue_out(_get(db, user, issue_id))


@router.put("/{issue_id}", response_model=IssueOut)
def update_issue(issue_id: int, payload: IssueUpdate, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    i = _get(db, user, issue_id)
    changes = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    for k, v in changes.items():
        setattr(i, k, v)
    if changes.get("status") == "Resolved":
        i.resolved_at = utcnow()
    elif "status" in changes:
        i.resolved_at = None
    a = i.appliance
    i.priority = compute_priority(i.severity, a.risk_level, bool(a.warranty_expiry and a.warranty_expiry >= date.today()))
    db.commit()
    predict_appliance(db, a)
    generate_alerts(db, user)
    db.refresh(i)
    return issue_out(i)


@router.post("/{issue_id}/image", response_model=IssueOut)
async def upload_issue_image(issue_id: int, file: UploadFile = File(...), user: User = Depends(get_current_user),
                             db: Session = Depends(get_db)):
    i = _get(db, user, issue_id)
    path = await save_image(file, f"issues/{user.id}")
    old = i.image_path
    i.image_path = path
    db.commit()
    delete_upload(old)
    db.refresh(i)
    return issue_out(i)


@router.delete("/{issue_id}", response_model=Message)
def delete_issue(issue_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    i = _get(db, user, issue_id)
    a = i.appliance
    img = i.image_path
    db.delete(i)
    db.commit()
    delete_upload(img)
    predict_appliance(db, a)
    return Message(message="Issue deleted")
