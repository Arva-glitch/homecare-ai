"""SQLAlchemy ORM models. Importing this package registers every table on Base.metadata."""
from app.models.enums import (  # noqa: F401
    APPLIANCE_CATEGORIES,
    CONDITIONS,
    EXPENSE_TYPES,
    ISSUE_STATUSES,
    MAINTENANCE_TYPES,
    PROBLEM_CATEGORIES,
    RISK_LEVELS,
    SCHEDULE_STATUSES,
    SEVERITIES,
    USAGE_FREQUENCIES,
)
from app.models.user import User  # noqa: F401
from app.models.appliance import Appliance  # noqa: F401
from app.models.maintenance import MaintenanceRecord, MaintenanceSchedule  # noqa: F401
from app.models.issue import ReportedIssue  # noqa: F401
from app.models.expense import Expense  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.chat import ChatHistory  # noqa: F401
from app.models.prediction import PredictionHistory  # noqa: F401
