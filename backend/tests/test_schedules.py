from datetime import datetime, timedelta


def _future(days=3):
    return (datetime.now() + timedelta(days=days)).replace(microsecond=0).isoformat()


def test_schedule_crud_and_views(client, auth, appliance):
    r = client.post("/api/schedules", json={"appliance_id": appliance["id"], "maintenance_type": "Inspection",
                                            "scheduled_at": _future(), "description": "Check noise"}, headers=auth)
    assert r.status_code == 201, r.text
    s = r.json()
    assert s["title"].startswith("Inspection") and s["status"] == "Scheduled"
    assert len(client.get("/api/schedules", params={"view": "upcoming"}, headers=auth).json()) == 1
    r = client.put(f"/api/schedules/{s['id']}", json={"technician": "Ravi", "priority": "High"}, headers=auth)
    assert r.json()["technician"] == "Ravi" and r.json()["priority"] == "High"


def test_status_flow_complete_creates_record_and_expense(client, auth, appliance):
    s = client.post("/api/schedules", json={"appliance_id": appliance["id"], "maintenance_type": "General Servicing",
                                            "scheduled_at": _future(1), "estimated_cost": 500}, headers=auth).json()
    r = client.patch(f"/api/schedules/{s['id']}/status", json={"status": "In Progress"}, headers=auth)
    assert r.json()["status"] == "In Progress"
    r = client.patch(f"/api/schedules/{s['id']}/status", json={"status": "Completed", "actual_cost": 650}, headers=auth)
    assert r.status_code == 200 and r.json()["completed_at"]
    detail = client.get(f"/api/appliances/{appliance['id']}", headers=auth).json()
    assert detail["maintenance_records"][0]["schedule_id"] == s["id"]
    assert detail["last_service_date"] == datetime.now().date().isoformat()
    assert detail["health_score"] >= appliance["health_score"]  # servicing improves health
    assert client.get("/api/expenses", headers=auth).json()[0]["amount"] == 650
    assert len(client.get("/api/schedules", params={"view": "completed"}, headers=auth).json()) == 1
    # Completed tasks can't change status
    r = client.patch(f"/api/schedules/{s['id']}/status", json={"status": "Scheduled"}, headers=auth)
    assert r.status_code == 400


def test_cancel(client, auth, appliance):
    s = client.post("/api/schedules", json={"appliance_id": appliance["id"], "maintenance_type": "Cleaning",
                                            "scheduled_at": _future()}, headers=auth).json()
    r = client.post(f"/api/schedules/{s['id']}/cancel", headers=auth)
    assert r.json()["status"] == "Cancelled"
    assert client.post(f"/api/schedules/{s['id']}/cancel", headers=auth).status_code == 400


def test_invalid_status_and_isolation(client, auth, other_auth, appliance):
    s = client.post("/api/schedules", json={"appliance_id": appliance["id"], "maintenance_type": "Cleaning",
                                            "scheduled_at": _future()}, headers=auth).json()
    r = client.patch(f"/api/schedules/{s['id']}/status", json={"status": "Done"}, headers=auth)
    assert r.status_code == 422
    assert client.get(f"/api/schedules/{s['id']}", headers=other_auth).status_code == 404
    r = client.post("/api/schedules", json={"appliance_id": appliance["id"], "maintenance_type": "Cleaning",
                                            "scheduled_at": _future()}, headers=other_auth)
    assert r.status_code == 404


def test_ai_suggestions_and_accept(client, auth, appliance):
    sugg = client.get("/api/schedules/suggestions", headers=auth).json()
    assert sugg and sugg[0]["appliance_id"] == appliance["id"]
    r = client.post("/api/schedules/suggestions/accept", json={"appliance_id": appliance["id"]}, headers=auth)
    assert r.status_code == 201 and r.json()["is_ai_suggested"] is True
    # Once scheduled it is no longer suggested
    assert client.get("/api/schedules/suggestions", headers=auth).json() == []
