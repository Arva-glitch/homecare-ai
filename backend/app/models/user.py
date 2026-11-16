from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30))
    address: Mapped[str | None] = mapped_column(String(500))
    household_name: Mapped[str | None] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Incremented on logout / password change to invalidate previously issued JWTs.
    token_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reset_token_hash: Mapped[str | None] = mapped_column(String(128), index=True)
    reset_token_expires: Mapped[datetime | None] = mapped_column(DateTime)

    appliances = relationship("Appliance", back_populates="owner", cascade="all, delete-orphan")
    schedules = relationship("MaintenanceSchedule", back_populates="user", cascade="all, delete-orphan")
    issues = relationship("ReportedIssue", back_populates="user", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")
    predictions = relationship("PredictionHistory", back_populates="user", cascade="all, delete-orphan")
    maintenance_records = relationship("MaintenanceRecord", back_populates="user", cascade="all, delete-orphan")
