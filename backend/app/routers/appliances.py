from typing import Literal
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_owned_appliance
from app.db.session import get_db
from app.models import Appliance, Expense, MaintenanceRecord, User
from app.models.enums import DEFAULT_LIFESPAN_YEARS
from app.schemas.appliance import (
    ApplianceCreate,
    ApplianceDetail,
    ApplianceList,
    ApplianceOut,
    ApplianceUpdate,
    MaintenanceRecordCreate,
    MaintenanceRecordOut,
)
from app.schemas.common import Message
from app.services.notification_service import generate_alerts
from app.services.prediction_service import predict_appliance
from app.services.serializers import appliance_out
from app.utils.files import delete_upload, save_image

router = APIRouter(prefix="/appliances", tags=["Appliances"])

SORT_FIELDS = {
    "name": Appliance.name, "category": Appliance.category, "purchase_date": Appliance.purchase_date,
    "health_score": Appliance.health_score, "created_at": Appliance.created_at,
    "last_service_date": Appliance.last_service_date, "warranty_expiry": Appliance.warranty_expiry,
}


@router.get("", response_model=ApplianceList)
def list_appliances(
    search: str | None = Query(None, description="Search name, brand, model number"),
    category: str | None = None,
    risk_level: str | None = None,
    condition: str | None = None,
    sort_by: Literal["name", "category", "purchase_date", "health_score", "created_at",
                     "last_service_date", "warranty_expiry"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = select(Appliance).where(Appliance.user_id == user.id)
    if search:
        like = f"%{search.strip()}%"
        q = q.where(or_(Appliance.name.ilike(like), Appliance.brand.ilike(like), Appliance.model_number.ilike(like)))
    if category:
        q = q.where(Appliance.category == category)
    if risk_level:
        q = q.where(Appliance.risk_level == risk_level)
    if condition:
        q = q.where(Appliance.condition == condition)
    col = SORT_FIELDS[sort_by]
    q = q.order_by(asc(col) if order == "asc" else desc(col), Appliance.id)
    items = db.scalars(q).all()
    return ApplianceList(items=[appliance_out(a) for a in items], total=len(items))


@router.post("", response_model=ApplianceOut, status_code=status.HTTP_201_CREATED)
def create_appliance(payload: ApplianceCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = payload.model_dump()
    if not data.get("expected_lifespan_years"):
        data["expected_lifespan_years"] = DEFAULT_LIFESPAN_YEARS.get(payload.category, 8)
    a = Appliance(user_id=user.id, **data)
    db.add(a)
    db.commit()
    predict_appliance(db, a)
    generate_alerts(db, user)
    db.refresh(a)
    return appliance_out(a)


@router.get("/{appliance_id}", response_model=ApplianceDetail)
def get_appliance(appliance_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = get_owned_appliance(db, user, appliance_id)
    base = appliance_out(a).model_dump()
    start = a.installation_date or a.purchase_date
    total = db.scalar(select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.appliance_id == a.id))
    return ApplianceDetail(
        **base,
        maintenance_records=[MaintenanceRecordOut.model_validate(r) for r in a.maintenance_records],
        open_issues=sum(1 for i in a.issues if i.status != "Resolved"),
        total_expenses=float(total or 0),
        warranty_active=(a.warranty_expiry >= date.today()) if a.warranty_expiry else None,
        age_years=round((date.today() - start).days / 365.25, 1) if start else None,
    )


@router.put("/{appliance_id}", response_model=ApplianceOut)
def update_appliance(appliance_id: int, payload: ApplianceUpdate, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    a = get_owned_appliance(db, user, appliance_id)
    changes = payload.model_dump(exclude_unset=True)
    for k in ("name", "category", "usage_frequency", "condition", "expected_lifespan_years"):
        if k in changes and changes[k] is None:
            changes.pop(k)
    for k, v in changes.items():
        setattr(a, k, v)
    if a.purchase_date and a.purchase_date > date.today():
        raise HTTPException(status_code=422, detail="purchase_date cannot be in the future")
    db.commit()
    predict_appliance(db, a)
    generate_alerts(db, user)
    db.refresh(a)
    return appliance_out(a)


@router.delete("/{appliance_id}", response_model=Message)
def delete_appliance(appliance_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = get_owned_appliance(db, user, appliance_id)
    image = a.image_path
    issue_images = [i.image_path for i in a.issues]
    db.delete(a)
    db.commit()
    for p in [image, *issue_images]:
        delete_upload(p)
    return Message(message="Appliance deleted")


@router.post("/{appliance_id}/image", response_model=ApplianceOut)
async def upload_image(appliance_id: int, file: UploadFile = File(...), user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    a = get_owned_appliance(db, user, appliance_id)
    path = await save_image(file, f"appliances/{user.id}")
    old = a.image_path
    a.image_path = path
    db.commit()
    delete_upload(old)
    db.refresh(a)
    return appliance_out(a)


@router.delete("/{appliance_id}/image", response_model=ApplianceOut)
def remove_image(appliance_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = get_owned_appliance(db, user, appliance_id)
    delete_upload(a.image_path)
    a.image_path = None
    db.commit()
    db.refresh(a)
    return appliance_out(a)


# ----- Maintenance history (records of maintenance that actually happened)

@router.get("/{appliance_id}/records", response_model=list[MaintenanceRecordOut])
def list_records(appliance_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = get_owned_appliance(db, user, appliance_id)
    return a.maintenance_records


@router.post("/{appliance_id}/records", response_model=MaintenanceRecordOut, status_code=201)
def add_record(appliance_id: int, payload: MaintenanceRecordCreate, user: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    a = get_owned_appliance(db, user, appliance_id)
    data = payload.model_dump(exclude={"add_expense"})
    r = MaintenanceRecord(user_id=user.id, appliance_id=a.id, **data)
    db.add(r)
    if not a.last_service_date or payload.service_date > a.last_service_date:
        a.last_service_date = payload.service_date
    if payload.add_expense and payload.cost > 0:
        etype = "Repair" if payload.was_breakdown or payload.maintenance_type == "Repair" else (
            "Parts" if payload.maintenance_type in ("Part Replacement", "Filter Change") else "Servicing")
        db.add(Expense(user_id=user.id, appliance_id=a.id, expense_type=etype, amount=payload.cost,
                       expense_date=payload.service_date, vendor=payload.technician,
                       description=f"{payload.maintenance_type}: {payload.description or ''}".strip(": ")))
    db.commit()
    db.refresh(r)
    predict_appliance(db, a)
    return r


@router.delete("/{appliance_id}/records/{record_id}", response_model=Message)
def delete_record(appliance_id: int, record_id: int, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    a = get_owned_appliance(db, user, appliance_id)
    r = db.get(MaintenanceRecord, record_id)
    if not r or r.appliance_id != a.id:
        raise HTTPException(status_code=404, detail="Record not found")
    db.delete(r)
    db.commit()
    predict_appliance(db, a)
    return Message(message="Record deleted")
