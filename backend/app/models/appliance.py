from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Appliance(TimestampMixin, Base):
    __tablename__ = "appliances"
    __table_args__ = (
        Index("ix_appliances_user_category", "user_id", "category"),
        Index("ix_appliances_user_risk", "user_id", "risk_level"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(80))
    model_number: Mapped[str | None] = mapped_column(String(80))
    purchase_date: Mapped[date | None] = mapped_column(Date)
    installation_date: Mapped[date | None] = mapped_column(Date)
    warranty_expiry: Mapped[date | None] = mapped_column(Date, index=True)
    expected_lifespan_years: Mapped[float] = mapped_column(Float, nullable=False, default=10)
    last_service_date: Mapped[date | None] = mapped_column(Date)
    usage_frequency: Mapped[str] = mapped_column(String(20), nullable=False, default="Medium")
    condition: Mapped[str] = mapped_column(String(20), nullable=False, default="Good")
    location: Mapped[str | None] = mapped_column(String(80))
    notes: Mapped[str | None] = mapped_column(Text)
    image_path: Mapped[str | None] = mapped_column(String(255))

    # Cached result of the most recent prediction (full history in prediction_history)
    health_score: Mapped[float | None] = mapped_column(Float)
    risk_level: Mapped[str | None] = mapped_column(String(20))
    next_service_date: Mapped[date | None] = mapped_column(Date)

    owner = relationship("User", back_populates="appliances")
    maintenance_records = relationship(
        "MaintenanceRecord", back_populates="appliance", cascade="all, delete-orphan",
        order_by="desc(MaintenanceRecord.service_date)",
    )
    schedules = relationship("MaintenanceSchedule", back_populates="appliance", cascade="all, delete-orphan")
    issues = relationship("ReportedIssue", back_populates="appliance", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="appliance")
    predictions = relationship("PredictionHistory", back_populates="appliance", cascade="all, delete-orphan")
