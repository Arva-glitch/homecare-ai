import calendar
from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import extract, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_owned_appliance
from app.db.session import get_db
from app.models import Expense, User
from app.models.enums import EXPENSE_TYPES
from app.schemas.common import Message
from app.schemas.expense import ExpenseCreate, ExpenseOut, ExpenseSummary, ExpenseUpdate
from app.services.serializers import expense_out

router = APIRouter(prefix="/expenses", tags=["Expenses"])


def _get(db: Session, user: User, expense_id: int) -> Expense:
    e = db.get(Expense, expense_id)
    if not e or e.user_id != user.id:
        raise HTTPException(status_code=404, detail="Expense not found")
    return e


@router.get("", response_model=list[ExpenseOut])
def list_expenses(
    appliance_id: int | None = None,
    expense_type: str | None = None,
    year: int | None = None,
    month: int | None = Query(None, ge=1, le=12),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = select(Expense).where(Expense.user_id == user.id)
    if appliance_id:
        q = q.where(Expense.appliance_id == appliance_id)
    if expense_type:
        q = q.where(Expense.expense_type == expense_type)
    if year:
        q = q.where(extract("year", Expense.expense_date) == year)
    if month:
        q = q.where(extract("month", Expense.expense_date) == month)
    q = q.order_by(Expense.expense_date.desc(), Expense.id.desc())
    return [expense_out(e) for e in db.scalars(q).all()]


@router.post("", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(payload: ExpenseCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.appliance_id:
        get_owned_appliance(db, user, payload.appliance_id)
    if payload.expense_date > date.today():
        raise HTTPException(status_code=422, detail="expense_date cannot be in the future")
    e = Expense(user_id=user.id, **payload.model_dump())
    db.add(e)
    db.commit()
    db.refresh(e)
    return expense_out(e)


@router.get("/summary", response_model=ExpenseSummary)
def summary(year: int | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Monthly / yearly reports, appliance-wise totals and the highest-cost appliance."""
    year = year or date.today().year
    expenses = db.scalars(select(Expense).where(Expense.user_id == user.id)).all()

    monthly = [{"month": calendar.month_abbr[m], "total": 0.0, **{t: 0.0 for t in EXPENSE_TYPES}} for m in range(1, 13)]
    yearly: dict[int, float] = defaultdict(float)
    by_app: dict = {}
    by_type: dict[str, float] = defaultdict(float)
    total_year = 0.0
    total_all = 0.0
    for e in expenses:
        amt = float(e.amount)
        total_all += amt
        yearly[e.expense_date.year] += amt
        if e.expense_date.year == year:
            total_year += amt
            m = monthly[e.expense_date.month - 1]
            m["total"] += amt
            m[e.expense_type] = m.get(e.expense_type, 0.0) + amt
            by_type[e.expense_type] += amt
        key = e.appliance_id or 0
        entry = by_app.setdefault(key, {"appliance_id": e.appliance_id,
                                        "appliance_name": e.appliance.name if e.appliance else "General / Unassigned",
                                        "total": 0.0, "year_total": 0.0, "count": 0})
        entry["total"] += amt
        entry["count"] += 1
        if e.expense_date.year == year:
            entry["year_total"] += amt

    for m in monthly:
        for k in list(m):
            if k != "month":
                m[k] = round(m[k], 2)
    by_appliance = sorted(({**v, "total": round(v["total"], 2), "year_total": round(v["year_total"], 2)}
                           for v in by_app.values()), key=lambda x: -x["total"])
    assigned = [x for x in by_appliance if x["appliance_id"]]
    return ExpenseSummary(
        year=year,
        total_all_time=round(total_all, 2),
        total_year=round(total_year, 2),
        monthly=monthly,
        yearly=[{"year": y, "total": round(t, 2)} for y, t in sorted(yearly.items())],
        by_appliance=by_appliance,
        by_type=[{"type": t, "total": round(v, 2)} for t, v in sorted(by_type.items(), key=lambda x: -x[1])],
        highest_cost_appliance=assigned[0] if assigned else None,
    )


@router.get("/{expense_id}", response_model=ExpenseOut)
def get_expense(expense_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return expense_out(_get(db, user, expense_id))


@router.put("/{expense_id}", response_model=ExpenseOut)
def update_expense(expense_id: int, payload: ExpenseUpdate, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    e = _get(db, user, expense_id)
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("appliance_id"):
        get_owned_appliance(db, user, changes["appliance_id"])
    if changes.get("expense_date") and changes["expense_date"] > date.today():
        raise HTTPException(status_code=422, detail="expense_date cannot be in the future")
    for k, v in changes.items():
        if v is not None or k in ("appliance_id", "vendor", "description"):
            setattr(e, k, v)
    db.commit()
    db.refresh(e)
    return expense_out(e)


@router.delete("/{expense_id}", response_model=Message)
def delete_expense(expense_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    e = _get(db, user, expense_id)
    db.delete(e)
    db.commit()
    return Message(message="Expense deleted")
