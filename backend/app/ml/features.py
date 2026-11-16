"""Feature engineering + transparent rule-based health analysis.

The same feature vector feeds both the Random Forest model and the rule-based
fallback, so the two paths are directly comparable.
"""
from dataclasses import asdict, dataclass
from datetime import date

from app.models.enums import DEFAULT_LIFESPAN_YEARS, SERVICE_INTERVAL_DAYS

FEATURE_NAMES = [
    "age_years",
    "lifespan_ratio",
    "usage_level",
    "days_since_service",
    "service_overdue_ratio",
    "services_last_2y",
    "breakdowns_total",
    "open_issues",
    "max_open_severity",
    "condition_level",
]

USAGE_LEVEL = {"Low": 0, "Medium": 1, "High": 2, "Very High": 3}
CONDITION_LEVEL = {"Excellent": 0, "Good": 1, "Fair": 2, "Poor": 3}
SEVERITY_LEVEL = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
SEVERITY_NAME = {v: k for k, v in SEVERITY_LEVEL.items()}

RISK_CLASSES = ["Low", "Medium", "High", "Critical"]
# Health score represented by each risk class when converting ML probabilities.
CLASS_HEALTH_CENTER = {"Low": 88.0, "Medium": 65.0, "High": 45.0, "Critical": 20.0}


@dataclass
class ApplianceFeatures:
    age_years: float
    lifespan_ratio: float
    usage_level: int
    days_since_service: int
    service_overdue_ratio: float
    services_last_2y: int
    breakdowns_total: int
    open_issues: int
    max_open_severity: int
    condition_level: int

    def to_vector(self) -> list[float]:
        return [float(getattr(self, n)) for n in FEATURE_NAMES]

    def to_dict(self) -> dict:
        return asdict(self)


def extract_features(appliance, records=None, issues=None, today: date | None = None) -> ApplianceFeatures:
    """Build model features from an Appliance ORM object and its history."""
    today = today or date.today()
    records = list(records if records is not None else appliance.maintenance_records)
    issues = list(issues if issues is not None else appliance.issues)

    start = appliance.installation_date or appliance.purchase_date or appliance.created_at.date()
    age_years = max(0.0, (today - start).days / 365.25)
    lifespan = appliance.expected_lifespan_years or DEFAULT_LIFESPAN_YEARS.get(appliance.category, 8)

    last_service = appliance.last_service_date
    record_dates = [r.service_date for r in records if r.service_date]
    if record_dates:
        latest = max(record_dates)
        if not last_service or latest > last_service:
            last_service = latest
    days_since = (today - (last_service or start)).days
    interval = SERVICE_INTERVAL_DAYS.get(appliance.category, 365)

    two_years_ago = today.toordinal() - 730
    services_2y = sum(1 for d in record_dates if d.toordinal() >= two_years_ago)
    if appliance.last_service_date and appliance.last_service_date.toordinal() >= two_years_ago and \
            appliance.last_service_date not in record_dates:
        services_2y += 1

    breakdowns = sum(1 for r in records if r.was_breakdown)
    open_issues = [i for i in issues if i.status != "Resolved"]
    max_sev = max((SEVERITY_LEVEL.get(i.severity, 0) for i in open_issues), default=0)

    return ApplianceFeatures(
        age_years=round(age_years, 2),
        lifespan_ratio=round(age_years / lifespan, 3) if lifespan else 0.0,
        usage_level=USAGE_LEVEL.get(appliance.usage_frequency, 1),
        days_since_service=max(0, days_since),
        service_overdue_ratio=round(max(0, days_since) / interval, 3),
        services_last_2y=services_2y,
        breakdowns_total=breakdowns,
        open_issues=len(open_issues),
        max_open_severity=max_sev,
        condition_level=CONDITION_LEVEL.get(appliance.condition, 1),
    )


def rule_based_analysis(f: ApplianceFeatures) -> tuple[float, list[dict]]:
    """Deduction-based health score (0-100) with a human-readable factor list.

    This is the rule-based fallback AND the explanation layer for ML predictions.
    """
    factors: list[dict] = []

    def add(name: str, detail: str, pts: float):
        if pts > 0:
            factors.append({"factor": name, "detail": detail, "impact": round(pts, 1)})

    # 1. Age relative to expected lifespan
    age_pts = min(30.0, 25.0 * f.lifespan_ratio) + (8.0 if f.lifespan_ratio > 1 else 0.0)
    age_pts = min(age_pts, 35.0)
    pct = round(f.lifespan_ratio * 100)
    add("Appliance age", f"{f.age_years:.1f} years old — about {pct}% of its expected lifespan"
        + (" (beyond expected lifespan)" if f.lifespan_ratio > 1 else ""), age_pts if pct >= 20 else 0)

    # 2. Usage frequency
    usage_pts = [0, 3, 7, 11][f.usage_level]
    add("Usage frequency", ["Low", "Medium", "High", "Very High"][f.usage_level] + " usage increases wear", usage_pts)

    # 3. Time since last servicing
    r = f.service_overdue_ratio
    svc_pts = 0.0 if r <= 0.6 else min(20.0, (r - 0.6) * 14.0)
    if r > 1:
        detail = f"Last serviced {f.days_since_service} days ago — overdue (about {r:.1f}x the recommended interval)"
    else:
        detail = f"Last serviced {f.days_since_service} days ago — service due soon"
    add("Time since last service", detail, svc_pts)

    # 4. Maintenance history
    if f.services_last_2y == 0:
        add("Maintenance history", "No servicing recorded in the last 2 years", 5.0)

    # 5. Previous breakdowns
    add("Previous breakdowns", f"{f.breakdowns_total} breakdown repair(s) on record", min(15.0, 5.0 * f.breakdowns_total))

    # 6. Reported problems
    if f.open_issues:
        sev_pts = {1: 4, 2: 8, 3: 14, 4: 22}.get(f.max_open_severity, 0)
        issue_pts = min(25.0, sev_pts + 3.0 * (f.open_issues - 1))
        add("Reported problems", f"{f.open_issues} unresolved issue(s), highest severity: "
            f"{SEVERITY_NAME.get(f.max_open_severity, 'n/a')}", issue_pts)

    # 7. Physical condition
    add("Condition", ["Excellent", "Good", "Fair", "Poor"][f.condition_level] + " condition reported by owner",
        [0, 3, 8, 15][f.condition_level])

    total = sum(x["impact"] for x in factors)
    health = max(0.0, min(100.0, 100.0 - total))
    factors.sort(key=lambda x: x["impact"], reverse=True)
    return round(health, 1), factors


def risk_from_health(health: float, f: ApplianceFeatures | None = None) -> str:
    if health >= 75:
        risk = "Low"
    elif health >= 55:
        risk = "Medium"
    elif health >= 35:
        risk = "High"
    else:
        risk = "Critical"
    # Safety override: an open Critical issue is never Low/Medium risk.
    if f is not None and f.max_open_severity >= 4 and RISK_CLASSES.index(risk) < 2:
        risk = "High"
    return risk
