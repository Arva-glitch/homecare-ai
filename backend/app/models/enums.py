"""Allowed values for enumerated string columns (validated in Pydantic schemas)."""

APPLIANCE_CATEGORIES = [
    "Refrigerator",
    "Air Conditioner",
    "Washing Machine",
    "Television",
    "Microwave",
    "Water Purifier",
    "Geyser",
    "Other",
]

USAGE_FREQUENCIES = ["Low", "Medium", "High", "Very High"]
CONDITIONS = ["Excellent", "Good", "Fair", "Poor"]
RISK_LEVELS = ["Low", "Medium", "High", "Critical"]
SEVERITIES = ["Low", "Medium", "High", "Critical"]

MAINTENANCE_TYPES = [
    "General Servicing",
    "Inspection",
    "Cleaning",
    "Repair",
    "Part Replacement",
    "Filter Change",
    "Gas Refill",
    "Installation",
    "Other",
]

SCHEDULE_STATUSES = ["Pending", "Scheduled", "In Progress", "Completed", "Cancelled"]
ISSUE_STATUSES = ["Open", "In Progress", "Resolved"]

PROBLEM_CATEGORIES = [
    "Unusual Noise",
    "Leakage",
    "Not Working / No Power",
    "Not Cooling",
    "Not Heating",
    "Electrical / Tripping",
    "Bad Odor",
    "Excess Vibration",
    "Display / Controls",
    "Water Quality",
    "High Power Consumption",
    "Other",
]

EXPENSE_TYPES = ["Repair", "Servicing", "Replacement", "Parts", "Other"]

# Recommended service interval (days) per category, used by predictions & scheduler.
SERVICE_INTERVAL_DAYS = {
    "Refrigerator": 365,
    "Air Conditioner": 180,
    "Washing Machine": 180,
    "Television": 730,
    "Microwave": 365,
    "Water Purifier": 90,
    "Geyser": 365,
    "Other": 365,
}

# Typical lifespan (years) used as a default when the user leaves it blank.
DEFAULT_LIFESPAN_YEARS = {
    "Refrigerator": 12,
    "Air Conditioner": 10,
    "Washing Machine": 10,
    "Television": 8,
    "Microwave": 8,
    "Water Purifier": 7,
    "Geyser": 10,
    "Other": 8,
}
