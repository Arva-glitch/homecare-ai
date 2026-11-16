"""Load DEMO data.

    python seed.py            # create demo users if they don't exist
    python seed.py --reset    # delete and recreate the demo users and all their data

Demo credentials (clearly for demonstration only):
    demo@homecare.ai   / Demo@1234   (fully populated household)
    priya@homecare.ai  / Demo@1234   (second household, used to show data isolation)
"""
import json
import sys
from datetime import date, datetime, time, timedelta

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.ml.predictor import predictor
from app.models import (
    Appliance,
    ChatHistory,
    Expense,
    MaintenanceRecord,
    MaintenanceSchedule,
    PredictionHistory,
    ReportedIssue,
    User,
)
from app.services.chat_service import issue_suggestions
from app.services.notification_service import generate_alerts
from app.services.prediction_service import predict_appliance
from app.utils.time import utcnow

DEMO_PASSWORD = "Demo@1234"
T = date.today()


def d(days_ago: int) -> date:
    return T - timedelta(days=days_ago)


def dt(days_ahead: int, hour: int = 10) -> datetime:
    return datetime.combine(T + timedelta(days=days_ahead), time(hour, 0))


def make_user(db, email, name, household):
    u = User(full_name=name, email=email, hashed_password=hash_password(DEMO_PASSWORD), household_name=household,
             phone="+91 98765 43210", address="Indore, Madhya Pradesh")
    db.add(u)
    db.flush()
    return u


def seed_main(db):
    u = make_user(db, "demo@homecare.ai", "Demo User", "Demo Household")

    specs = [
        dict(name="Kitchen Refrigerator", category="Refrigerator", brand="LG", model_number="GL-T302RPZY",
             purchase_date=d(9 * 365), installation_date=d(9 * 365 - 3), warranty_expiry=d(8 * 365),
             expected_lifespan_years=12, last_service_date=d(420), usage_frequency="Very High", condition="Fair",
             location="Kitchen", notes="Double-door frost-free. Compressor replaced once."),
        dict(name="Bedroom Split AC", category="Air Conditioner", brand="Daikin", model_number="FTKF50TV",
             purchase_date=d(3 * 365), installation_date=d(3 * 365 - 2), warranty_expiry=T + timedelta(days=21),
             expected_lifespan_years=10, last_service_date=d(250), usage_frequency="High", condition="Good",
             location="Master bedroom"),
        dict(name="Front-Load Washing Machine", category="Washing Machine", brand="Samsung", model_number="WW70T4020CE",
             purchase_date=d(6 * 365), installation_date=d(6 * 365), warranty_expiry=d(4 * 365),
             expected_lifespan_years=10, last_service_date=d(300), usage_frequency="High", condition="Fair",
             location="Utility area"),
        dict(name="RO Water Purifier", category="Water Purifier", brand="Kent", model_number="Grand Plus",
             purchase_date=d(2 * 365), installation_date=d(2 * 365), warranty_expiry=d(365),
             expected_lifespan_years=7, last_service_date=d(40), usage_frequency="Very High", condition="Good",
             location="Kitchen"),
        dict(name="Convection Microwave", category="Microwave", brand="IFB", model_number="25BC4",
             purchase_date=d(400), installation_date=d(400), warranty_expiry=T + timedelta(days=330),
             expected_lifespan_years=8, last_service_date=None, usage_frequency="Medium", condition="Excellent",
             location="Kitchen"),
        dict(name="Bathroom Geyser", category="Geyser", brand="Bajaj", model_number="Shakti 15L",
             purchase_date=d(5 * 365), installation_date=d(5 * 365), warranty_expiry=d(3 * 365),
             expected_lifespan_years=10, last_service_date=d(500), usage_frequency="Medium", condition="Good",
             location="Bathroom"),
        dict(name="Living Room Smart TV", category="Television", brand="Sony", model_number="KD-55X75K",
             purchase_date=d(700), installation_date=d(698), warranty_expiry=d(335),
             expected_lifespan_years=8, last_service_date=None, usage_frequency="High", condition="Excellent",
             location="Living room"),
    ]
    apps = {}
    for s in specs:
        a = Appliance(user_id=u.id, **s)
        db.add(a)
        db.flush()
        apps[s["category"]] = a

    fridge, ac, wm = apps["Refrigerator"], apps["Air Conditioner"], apps["Washing Machine"]
    ro, mw, gy, tv = apps["Water Purifier"], apps["Microwave"], apps["Geyser"], apps["Television"]

    records = [
        (fridge, d(1500), "Repair", "Compressor replaced after cooling failure", "CoolFix Services", 6500, True),
        (fridge, d(800), "Repair", "Door gasket replaced", "CoolFix Services", 1200, True),
        (fridge, d(420), "General Servicing", "Coil cleaning and thermostat check", "CoolFix Services", 650, False),
        (ac, d(610), "General Servicing", "Pre-summer jet wash", "AirCare Pros", 799, False),
        (ac, d(250), "Gas Refill", "R32 top-up after weak cooling", "AirCare Pros", 2800, False),
        (wm, d(900), "Repair", "Drain pump replaced", "Samsung Service Centre", 2200, True),
        (wm, d(300), "Cleaning", "Drum and filter cleaning", "Samsung Service Centre", 500, False),
        (ro, d(220), "Filter Change", "Sediment + carbon filter replaced", "Kent Care", 1500, False),
        (ro, d(40), "Filter Change", "RO membrane replaced", "Kent Care", 2400, False),
        (gy, d(500), "Inspection", "Descaling and anode check", "Local electrician", 450, False),
    ]
    for a, when, mtype, desc, tech, cost, brk in records:
        db.add(MaintenanceRecord(user_id=u.id, appliance_id=a.id, service_date=when, maintenance_type=mtype,
                                 description=desc, technician=tech, cost=cost, was_breakdown=brk))
        etype = "Repair" if brk or mtype == "Repair" else ("Parts" if mtype in ("Filter Change",) else "Servicing")
        db.add(Expense(user_id=u.id, appliance_id=a.id, expense_type=etype, amount=cost, expense_date=when,
                       vendor=tech, description=f"{mtype}: {desc}"))

    # Extra expenses spread across the last 12 months for charts
    extras = [
        (tv, d(330), "Parts", 1499, "Wall-mount bracket"),
        (mw, d(180), "Other", 350, "Cleaning kit and microwave-safe cover"),
        (ac, d(150), "Servicing", 799, "Mid-season filter cleaning"),
        (wm, d(95), "Parts", 650, "New inlet hose"),
        (gy, d(60), "Repair", 900, "Thermostat replaced"),
        (fridge, d(25), "Servicing", 400, "Water dispenser line flushed"),
        (None, d(12), "Other", 600, "Voltage stabiliser for kitchen line"),
        (ro, d(5), "Servicing", 300, "TDS check visit"),
    ]
    for a, when, etype, amt, desc in extras:
        db.add(Expense(user_id=u.id, appliance_id=a.id if a else None, expense_type=etype, amount=amt,
                       expense_date=when, description=desc))

    db.flush()
    # Reported issues (AI suggestions generated by the same service the API uses)
    issue_specs = [
        (fridge, "Unusual Noise", "Loud buzzing and clicking from the back of the fridge, mostly at night.", "High", d(6), "Open"),
        (wm, "Leakage", "Water collects under the machine during the spin cycle.", "Medium", d(10), "Open"),
        (ac, "Not Cooling", "Cooling was weak last summer; resolved after gas refill.", "Medium", d(260), "Resolved"),
    ]
    for a, cat, desc, sev, when, st in issue_specs:
        text, src = issue_suggestions(a, cat, desc, sev)
        p = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}[sev]
        db.add(ReportedIssue(user_id=u.id, appliance_id=a.id, problem_category=cat, description=desc, severity=sev,
                             priority=f"P{p}", status=st, reported_date=when, ai_suggestions=text,
                             suggestion_source=src,
                             resolved_at=datetime.combine(d(250), time(6)) if st == "Resolved" else None))

    # Maintenance schedules
    sched = [
        (ac, "Pre-summer AC servicing", "General Servicing", dt(5), "Scheduled", "High", "AirCare Pros", 799, False),
        (fridge, "Fridge compressor & noise inspection", "Repair", dt(2, 16), "Pending", "Urgent", None, 1500, True),
        (gy, "Geyser annual inspection", "Inspection", dt(18), "Scheduled", "Normal", "Local electrician", 450, False),
        (ro, "RO sediment filter change", "Filter Change", dt(45), "Scheduled", "Low", "Kent Care", 800, False),
        (wm, "Washing machine drum cleaning", "Cleaning", dt(-3), "Scheduled", "Normal", None, 500, False),
        (ac, "Mid-season AC filter cleaning", "Cleaning", dt(-150), "Completed", "Normal", "AirCare Pros", 799, False),
        (ro, "RO membrane replacement", "Filter Change", dt(-40), "Completed", "High", "Kent Care", 2400, False),
        (tv, "TV wall-mount check", "Inspection", dt(-60), "Cancelled", "Low", None, None, False),
    ]
    for a, title, mtype, when, st, pr, tech, cost, ai in sched:
        db.add(MaintenanceSchedule(user_id=u.id, appliance_id=a.id, title=title, maintenance_type=mtype,
                                   scheduled_at=when, status=st, priority=pr, technician=tech, estimated_cost=cost,
                                   is_ai_suggested=ai, description="Booked via demo data",
                                   completed_at=when if st == "Completed" else None))
    db.commit()

    # Historic predictions (backdated) to show a trend, then a live prediction for each appliance
    for a in apps.values():
        db.refresh(a)
        live = predict_appliance(db, a)
        for back, drift in ((90, 9), (45, 4)):
            past = PredictionHistory(
                user_id=u.id, appliance_id=a.id, health_score=min(100, round(live.health_score + drift, 1)),
                risk_level=live.risk_level, priority=live.priority,
                recommended_service_date=live.recommended_service_date, model_used=live.model_used,
                confidence=live.confidence,
                explanation=json.dumps({"lines": ["Historical assessment (demo data)."], "factors": []}),
                features=live.features,
            )
            db.add(past)
            db.flush()
            past.created_at = utcnow() - timedelta(days=back)
            past.updated_at = past.created_at
    db.commit()

    sid = "demo-session-1"
    db.add(ChatHistory(user_id=u.id, session_id=sid, role="user", message="When should I service my AC?"))
    db.add(ChatHistory(user_id=u.id, session_id=sid, role="assistant", source="rules",
                       message="An air conditioner should generally be serviced about every **6 months**. "
                               "Your Bedroom Split AC is due soon — it's already booked in the Maintenance Scheduler."))
    db.commit()
    generate_alerts(db, u)
    return u


def seed_second(db):
    u = make_user(db, "priya@homecare.ai", "Priya Sharma", "Sharma Residence")
    for s in [
        dict(name="Single-Door Fridge", category="Refrigerator", brand="Whirlpool", purchase_date=d(4 * 365),
             expected_lifespan_years=12, last_service_date=d(200), usage_frequency="Medium", condition="Good"),
        dict(name="Window AC", category="Air Conditioner", brand="Voltas", purchase_date=d(8 * 365),
             expected_lifespan_years=10, last_service_date=d(700), usage_frequency="High", condition="Poor"),
    ]:
        a = Appliance(user_id=u.id, **s)
        db.add(a)
        db.commit()
        predict_appliance(db, a)
    generate_alerts(db, u)
    return u


def main():
    reset = "--reset" in sys.argv
    predictor.load()
    db = SessionLocal()
    try:
        for email, fn in (("demo@homecare.ai", seed_main), ("priya@homecare.ai", seed_second)):
            existing = db.scalar(select(User).where(User.email == email))
            if existing and not reset:
                print(f"{email} already exists (use --reset to recreate)")
                continue
            if existing:
                db.delete(existing)
                db.commit()
            fn(db)
            print(f"Seeded {email}")
        print(f"\nDemo login: demo@homecare.ai / {DEMO_PASSWORD}\nSecond user: priya@homecare.ai / {DEMO_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
