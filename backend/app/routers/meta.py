from fastapi import APIRouter

from app.models import enums

router = APIRouter(prefix="/meta", tags=["Reference data"])


@router.get("/options")
def options():
    """Allowed values for dropdowns (single source of truth shared with the frontend)."""
    return {
        "appliance_categories": enums.APPLIANCE_CATEGORIES,
        "usage_frequencies": enums.USAGE_FREQUENCIES,
        "conditions": enums.CONDITIONS,
        "risk_levels": enums.RISK_LEVELS,
        "severities": enums.SEVERITIES,
        "maintenance_types": enums.MAINTENANCE_TYPES,
        "schedule_statuses": enums.SCHEDULE_STATUSES,
        "issue_statuses": enums.ISSUE_STATUSES,
        "problem_categories": enums.PROBLEM_CATEGORIES,
        "expense_types": enums.EXPENSE_TYPES,
        "service_interval_days": enums.SERVICE_INTERVAL_DAYS,
        "default_lifespan_years": enums.DEFAULT_LIFESPAN_YEARS,
    }
