from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class MaintenanceRecord(TimestampMixin, Base):
    """A maintenance event that has actually happened (the appliance's maintenance history)."""

    __tablename__ = "maintenance_records"
    __table_args__ = (Index("ix_records_appliance_date", "appliance_id", "service_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    appliance_id: Mapped[int] = mapped_column(ForeignKey("appliances.id", ondelete="CASCADE"), nullable=False)
    schedule_id: Mapped[int | None] = mapped_column(ForeignKey("maintenance_schedules.id", ondelete="SET NULL"))
    service_date: Mapped[date] = mapped_column(Date, nullable=False)
    maintenance_type: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    technician: Mapped[str | None] = mapped_column(String(120))
    cost: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    was_breakdown: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="maintenance_records")
    appliance = relationship("Appliance", back_populates="maintenance_records")


class MaintenanceSchedule(TimestampMixin, Base):
    """A planned maintenance task."""

    __tablename__ = "maintenance_schedules"
    __table_args__ = (
        Index("ix_schedules_user_status", "user_id", "status"),
        Index("ix_schedules_user_date", "user_id", "scheduled_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    appliance_id: Mapped[int] = mapped_column(ForeignKey("appliances.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    maintenance_type: Mapped[str] = mapped_column(String(40), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="Scheduled", nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="Normal", nullable=False)
    technician: Mapped[str | None] = mapped_column(String(120))
    estimated_cost: Mapped[float | None] = mapped_column(Numeric(10, 2))
    is_ai_suggested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    user = relationship("User", back_populates="schedules")
    appliance = relationship("Appliance", back_populates="schedules")
