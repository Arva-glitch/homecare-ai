from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class PredictionHistory(TimestampMixin, Base):
    __tablename__ = "prediction_history"
    __table_args__ = (Index("ix_predictions_appliance_created", "appliance_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    appliance_id: Mapped[int] = mapped_column(ForeignKey("appliances.id", ondelete="CASCADE"), nullable=False)
    health_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    priority: Mapped[str] = mapped_column(String(60), nullable=False)
    recommended_service_date: Mapped[date] = mapped_column(Date, nullable=False)
    model_used: Mapped[str] = mapped_column(String(40), nullable=False)  # "random_forest" | "rule_based"
    confidence: Mapped[float | None] = mapped_column(Float)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list of reasons
    features: Mapped[str | None] = mapped_column(Text)  # JSON snapshot of model inputs

    user = relationship("User", back_populates="predictions")
    appliance = relationship("Appliance", back_populates="predictions")
