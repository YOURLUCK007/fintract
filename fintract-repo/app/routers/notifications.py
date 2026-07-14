"""Notification endpoints: list and mark-as-read."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Notification, User
from ..schemas import NotificationOut

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
def list_notifications(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return (
        db.query(Notification)
        .filter(Notification.user_id == current.id)
        .order_by(desc(Notification.created_at))
        .limit(50)
        .all()
    )


@router.post("/{notif_id}/read", response_model=NotificationOut)
def mark_read(notif_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    n = db.query(Notification).filter(Notification.id == notif_id, Notification.user_id == current.id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.is_read = True
    db.commit()
    db.refresh(n)
    return n
