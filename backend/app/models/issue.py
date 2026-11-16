from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class ReportedIssue(TimestampMixin, Base):
    __tablename__ = "reported_issues"
    __table_args__ = (Index("ix_issues_user_status", "user_id", "status"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    appliance_id: Mapped[int] = mapped_column(ForeignKey("appliances.id", ondelete="CASCADE"), index=True, nullable=False)
    problem_category: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    priority: Mapped[str] = mapped_column(String(10), nullable=False)  # P1 (highest) .. P4
    status: Mapped[str] = mapped_column(String(20), default="Open", nullable=False)
    reported_date: Mapped[date] = mapped_column(Date, nullable=False)
    image_path: Mapped[str | None] = mapped_column(String(255))
    ai_suggestions: Mapped[str | None] = mapped_column(Text)
    suggestion_source: Mapped[str | None] = mapped_column(String(20))  # "llm" or "rules"
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)

    user = relationship("User", back_populates="issues")
    appliance = relationship("Appliance", back_populates="issues")
