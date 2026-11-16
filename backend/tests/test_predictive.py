from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from app.ml.features import ApplianceFeatures, extract_features, risk_from_health, rule_based_analysis
from app.ml.predictor import RiskPredictor
from app.ml.synthetic_data import generate_synthetic_dataset
from app.ml.train import train


def feats(**kw):
    base = dict(age_years=1, lifespan_ratio=0.1, usage_level=1, days_since_service=30, service_overdue_ratio=0.1,
                services_last_2y=2, breakdowns_total=0, open_issues=0, max_open_severity=0, condition_level=0)
    base.update(kw)
    return ApplianceFeatures(**base)


def test_rule_scores_ordered():
    healthy, _ = rule_based_analysis(feats())
    worn, factors = rule_based_analysis(feats(age_years=11, lifespan_ratio=1.1, usage_level=3,
                                              days_since_service=900, service_overdue_ratio=2.5,
                                              services_last_2y=0, breakdowns_total=3, open_issues=2,
                                              max_open_severity=4, condition_level=3))
    assert healthy > 90 and worn < 20
    assert factors and factors[0]["impact"] >= factors[-1]["impact"]
    assert risk_from_health(healthy) == "Low" and risk_from_health(worn) == "Critical"


def test_critical_issue_override():
    f = feats(open_issues=1, max_open_severity=4)
    h, _ = rule_based_analysis(f)
    assert risk_from_health(h, f) in ("High", "Critical")


def test_synthetic_dataset_shape_and_label():
    df = generate_synthetic_dataset(500, seed=1)
    assert len(df) == 500
    assert set(df["risk_level"].astype(str)) <= {"Low", "Medium", "High", "Critical"}
    assert df["risk_level"].astype(str).nunique() >= 3


def test_model_trains_and_beats_chance():
    out = train(n_samples=1500, seed=7, save=False, verbose=False)
    assert out["meta"]["holdout_accuracy"] > 0.5  # 4 classes => chance ~0.25
    assert "SYNTHETIC" in out["meta"]["trained_on"]


@pytest.mark.parametrize("force_rules", [False, True])
def test_predictor_ml_and_fallback(force_rules):
    p = RiskPredictor()
    p.load()
    p.force_rules = force_rules
    good = p.predict(feats(), "Refrigerator", date.today() - timedelta(days=30))
    bad = p.predict(feats(age_years=13, lifespan_ratio=1.3, usage_level=3, days_since_service=1000,
                          service_overdue_ratio=2.7, services_last_2y=0, breakdowns_total=3, open_issues=2,
                          max_open_severity=4, condition_level=3), "Refrigerator", None)
    assert good.model_used == ("rule_based" if force_rules else "random_forest")
    assert 0 <= bad.health_score < good.health_score <= 100
    assert bad.risk_level in ("High", "Critical") and good.risk_level in ("Low", "Medium")
    assert bad.recommended_service_date <= date.today() + timedelta(days=14)
    assert good.recommended_service_date > date.today()
    assert any("SYNTHETIC" in line or "rule-based" in line for line in good.explanation)


def test_extract_features_from_appliance():
    today = date(2025, 1, 1)
    a = SimpleNamespace(installation_date=date(2020, 1, 1), purchase_date=None, created_at=None,
                        expected_lifespan_years=10, category="Air Conditioner", last_service_date=date(2024, 1, 1),
                        usage_frequency="High", condition="Good", maintenance_records=[], issues=[])
    rec = SimpleNamespace(service_date=date(2024, 7, 1), was_breakdown=True)
    issue = SimpleNamespace(status="Open", severity="High")
    f = extract_features(a, [rec], [issue], today=today)
    assert round(f.age_years) == 5 and f.days_since_service == (today - date(2024, 7, 1)).days
    assert f.breakdowns_total == 1 and f.open_issues == 1 and f.max_open_severity == 3
    assert f.usage_level == 2


def test_prediction_api(client, auth, appliance):
    r = client.post("/api/predictions/run", headers=auth)
    assert r.status_code == 200 and len(r.json()) == 1
    p = r.json()[0]
    assert 0 <= p["health_score"] <= 100 and p["explanation"] and p["factors"]
    latest = client.get("/api/predictions/latest", headers=auth).json()
    assert latest[0]["appliance_id"] == appliance["id"]
    hist = client.get("/api/predictions/history", params={"appliance_id": appliance["id"]}, headers=auth).json()
    assert len(hist) >= 2  # one on create + one now
    info = client.get("/api/predictions/model-info", headers=auth).json()
    assert info["ml_available"] and "SYNTHETIC" in info["trained_on"]


def test_issue_report_updates_risk(client, auth, appliance):
    before = appliance["health_score"]
    r = client.post("/api/issues", json={"appliance_id": appliance["id"], "problem_category": "Unusual Noise",
                                         "description": "Loud grinding noise from the back", "severity": "Critical"},
                    headers=auth)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["prediction"]["health_score"] < before
    assert body["prediction"]["risk_level"] in ("High", "Critical")
    assert body["issue"]["priority"] == "P1"
    assert "Possible causes" in body["issue"]["ai_suggestions"]
    assert body["recommended_schedule"]["maintenance_type"] == "Repair"
    notes = client.get("/api/notifications", headers=auth).json()
    assert any(n["type"] == "critical_issue" for n in notes["items"])
