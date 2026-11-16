from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import Notification, User
from app.schemas.common import Message
from app.schemas.misc import NotificationList, NotificationOut
from app.services.notification_service import generate_alerts

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _unread(db: Session, user: User) -> int:
    return db.scalar(select(func.count(Notification.id)).where(
        Notification.user_id == user.id, Notification.is_read.is_(False))) or 0


@router.get("", response_model=NotificationList)
def list_notifications(unread_only: bool = False, type: str | None = None, limit: int = Query(100, le=500),
                       user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        q = q.where(Notification.is_read.is_(False))
    if type:
        q = q.where(Notification.type == type)
    q = q.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(limit)
    items = db.scalars(q).all()
    return NotificationList(items=[NotificationOut.model_validate(n) for n in items], unread_count=_unread(db, user))


@router.get("/unread-count")
def unread_count(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"unread_count": _unread(db, user)}


@router.post("/refresh")
def refresh(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Scan appliances, schedules and issues and create any new alerts."""
    created = generate_alerts(db, user)
    return {"created": created, "unread_count": _unread(db, user)}


@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_read(notification_id: int, read: bool = True, user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    n = db.get(Notification, notification_id)
    if not n or n.user_id != user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.is_read = read
    db.commit()
    db.refresh(n)
    return n


@router.post("/read-all", response_model=Message)
def mark_all_read(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.execute(update(Notification).where(Notification.user_id == user.id).values(is_read=True))
    db.commit()
    return Message(message="All notifications marked as read")


@router.delete("/{notification_id}", response_model=Message)
def delete_notification(notification_id: int, user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    n = db.get(Notification, notification_id)
    if not n or n.user_id != user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    db.delete(n)
    db.commit()
    return Message(message="Notification deleted")
