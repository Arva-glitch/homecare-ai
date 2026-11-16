"""Integration tests for expenses, notifications, chatbot and dashboard."""
from datetime import date, datetime, timedelta


def test_expense_crud_and_summary(client, auth, appliance):
    y = date.today().year
    payload = {"appliance_id": appliance["id"], "expense_type": "Repair", "amount": 1200.5,
               "expense_date": date.today().isoformat(), "vendor": "FixIt"}
    e = client.post("/api/expenses", json=payload, headers=auth).json()
    client.post("/api/expenses", json={**payload, "appliance_id": None, "expense_type": "Other", "amount": 100},
                headers=auth)
    r = client.put(f"/api/expenses/{e['id']}", json={"amount": 1500}, headers=auth)
    assert r.json()["amount"] == 1500
    s = client.get("/api/expenses/summary", params={"year": y}, headers=auth).json()
    assert s["total_year"] == 1600
    assert s["highest_cost_appliance"]["appliance_name"] == "Kitchen Fridge"
    assert sum(m["total"] for m in s["monthly"]) == 1600
    assert client.delete(f"/api/expenses/{e['id']}", headers=auth).status_code == 200
    assert len(client.get("/api/expenses", headers=auth).json()) == 1


def test_expense_validation(client, auth):
    r = client.post("/api/expenses", json={"expense_type": "Repair", "amount": -5, "expense_date": "2024-01-01"},
                    headers=auth)
    assert r.status_code == 422


def test_notifications_generated_and_managed(client, auth, appliance):
    client.put(f"/api/appliances/{appliance['id']}",
               json={"warranty_expiry": (date.today() + timedelta(days=10)).isoformat()}, headers=auth)
    client.post("/api/schedules", json={"appliance_id": appliance["id"], "maintenance_type": "Inspection",
                                        "scheduled_at": (datetime.now() + timedelta(days=2)).isoformat()},
                headers=auth)
    client.post("/api/notifications/refresh", headers=auth)
    data = client.get("/api/notifications", headers=auth).json()
    types = {n["type"] for n in data["items"]}
    assert {"warranty", "upcoming_service"} <= types
    # Idempotent: refreshing again creates nothing new
    assert client.post("/api/notifications/refresh", headers=auth).json()["created"] == 0
    nid = data["items"][0]["id"]
    assert client.patch(f"/api/notifications/{nid}/read", headers=auth).json()["is_read"] is True
    client.post("/api/notifications/read-all", headers=auth)
    assert client.get("/api/notifications/unread-count", headers=auth).json()["unread_count"] == 0
    assert client.delete(f"/api/notifications/{nid}", headers=auth).status_code == 200


def test_chatbot_rule_based(client, auth, appliance):
    r = client.post("/api/chat", json={"message": "Why is my refrigerator making unusual noise?"}, headers=auth)
    assert r.status_code == 200
    body = r.json()
    assert body["reply"]["source"] == "rules" and body["llm_enabled"] is False
    assert "Kitchen Fridge" in body["reply"]["message"] and "Possible causes" in body["reply"]["message"]
    sid = body["session_id"]
    r = client.post("/api/chat", json={"message": "Which appliance requires immediate maintenance?", "session_id": sid},
                    headers=auth)
    assert "Kitchen Fridge" in r.json()["reply"]["message"]
    for q in ["When should I service my AC?", "How can I reduce electricity consumption?",
              "What maintenance tasks should I perform this month?", "Why is my washing machine leaking?"]:
        msg = client.post("/api/chat", json={"message": q, "session_id": sid}, headers=auth).json()["reply"]["message"]
        assert len(msg) > 40
    hist = client.get("/api/chat/history", params={"session_id": sid}, headers=auth).json()
    assert len(hist) == 12 and hist[0]["role"] == "user"
    sessions = client.get("/api/chat/sessions", headers=auth).json()
    assert sessions[0]["session_id"] == sid
    assert client.delete(f"/api/chat/sessions/{sid}", headers=auth).status_code == 200
    assert client.get("/api/chat/history", params={"session_id": sid}, headers=auth).json() == []


def test_dashboard_from_db(client, auth, other_auth, appliance):
    client.post("/api/expenses", json={"appliance_id": appliance["id"], "expense_type": "Servicing", "amount": 400,
                                       "expense_date": date.today().isoformat()}, headers=auth)
    d = client.get("/api/dashboard/summary", headers=auth).json()
    assert d["stats"]["total_appliances"] == 1
    assert d["stats"]["total_expenses"] == 400
    assert sum(x["count"] for x in d["health_distribution"]) == 1
    assert len(d["monthly_expenses"]) == 12 and d["monthly_expenses"][-1]["total"] == 400
    assert d["recent_activities"]
    # Another user sees an empty dashboard
    o = client.get("/api/dashboard/summary", headers=other_auth).json()
    assert o["stats"]["total_appliances"] == 0 and o["stats"]["total_expenses"] == 0


def test_meta_options(client):
    r = client.get("/api/meta/options")
    assert "Refrigerator" in r.json()["appliance_categories"]
