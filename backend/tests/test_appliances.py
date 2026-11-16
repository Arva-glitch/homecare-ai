import io

from tests.conftest import APPLIANCE

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def test_create_runs_prediction(client, auth, appliance):
    assert appliance["health_score"] is not None
    assert appliance["risk_level"] in ("Low", "Medium", "High", "Critical")
    assert appliance["next_service_date"]


def test_list_search_filter_sort(client, auth, appliance):
    client.post("/api/appliances", json={**APPLIANCE, "name": "Bedroom AC", "category": "Air Conditioner",
                                         "brand": "Daikin", "condition": "Excellent", "usage_frequency": "Low",
                                         "purchase_date": "2024-01-01", "installation_date": None,
                                         "last_service_date": "2024-06-01"}, headers=auth)
    r = client.get("/api/appliances", headers=auth)
    assert r.json()["total"] == 2
    r = client.get("/api/appliances", params={"search": "daik"}, headers=auth)
    assert [a["name"] for a in r.json()["items"]] == ["Bedroom AC"]
    r = client.get("/api/appliances", params={"category": "Refrigerator"}, headers=auth)
    assert r.json()["total"] == 1
    r = client.get("/api/appliances", params={"sort_by": "name", "order": "asc"}, headers=auth)
    assert [a["name"] for a in r.json()["items"]] == ["Bedroom AC", "Kitchen Fridge"]


def test_get_update_delete(client, auth, appliance):
    aid = appliance["id"]
    r = client.get(f"/api/appliances/{aid}", headers=auth)
    assert r.status_code == 200 and r.json()["warranty_active"] is False
    r = client.put(f"/api/appliances/{aid}", json={"condition": "Poor", "brand": "Samsung"}, headers=auth)
    assert r.status_code == 200 and r.json()["brand"] == "Samsung"
    assert r.json()["health_score"] <= appliance["health_score"]
    assert client.delete(f"/api/appliances/{aid}", headers=auth).status_code == 200
    assert client.get(f"/api/appliances/{aid}", headers=auth).status_code == 404


def test_validation(client, auth):
    r = client.post("/api/appliances", json={**APPLIANCE, "category": "Spaceship"}, headers=auth)
    assert r.status_code == 422
    r = client.post("/api/appliances", json={**APPLIANCE, "purchase_date": "2999-01-01"}, headers=auth)
    assert r.status_code == 422


def test_other_user_cannot_access(client, auth, other_auth, appliance):
    aid = appliance["id"]
    assert client.get(f"/api/appliances/{aid}", headers=other_auth).status_code == 404
    assert client.put(f"/api/appliances/{aid}", json={"name": "hack"}, headers=other_auth).status_code == 404
    assert client.delete(f"/api/appliances/{aid}", headers=other_auth).status_code == 404
    assert client.get("/api/appliances", headers=other_auth).json()["total"] == 0


def test_image_upload(client, auth, appliance):
    aid = appliance["id"]
    r = client.post(f"/api/appliances/{aid}/image", files={"file": ("a.png", io.BytesIO(PNG), "image/png")},
                    headers=auth)
    assert r.status_code == 200 and r.json()["image_url"].startswith("/uploads/")
    assert client.get(r.json()["image_url"]).status_code == 200
    bad = client.post(f"/api/appliances/{aid}/image", files={"file": ("a.png", io.BytesIO(b"notimage"), "image/png")},
                      headers=auth)
    assert bad.status_code == 400
    txt = client.post(f"/api/appliances/{aid}/image", files={"file": ("a.txt", io.BytesIO(b"x"), "text/plain")},
                      headers=auth)
    assert txt.status_code == 400


def test_maintenance_record_updates_history_and_expense(client, auth, appliance):
    aid = appliance["id"]
    r = client.post(f"/api/appliances/{aid}/records", json={
        "service_date": "2024-05-01", "maintenance_type": "General Servicing", "cost": 750, "technician": "Ravi"},
        headers=auth)
    assert r.status_code == 201
    detail = client.get(f"/api/appliances/{aid}", headers=auth).json()
    assert detail["last_service_date"] == "2024-05-01"
    assert len(detail["maintenance_records"]) == 1
    assert detail["total_expenses"] == 750
    exp = client.get("/api/expenses", headers=auth).json()
    assert exp[0]["expense_type"] == "Servicing" and exp[0]["amount"] == 750
