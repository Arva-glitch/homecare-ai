from tests.conftest import register


def test_register_login_me(client):
    data = register(client)
    assert data["user"]["email"] == "alice@example.com"
    r = client.post("/api/auth/login", json={"email": "ALICE@example.com", "password": "Passw0rd!"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200 and me.json()["full_name"] == "Alice Tester"


def test_duplicate_email_rejected(client):
    register(client)
    r = client.post("/api/auth/register", json={"full_name": "X Y", "email": "alice@example.com", "password": "Passw0rd!"})
    assert r.status_code == 409


def test_weak_password_rejected(client):
    r = client.post("/api/auth/register", json={"full_name": "X Y", "email": "x@example.com", "password": "short"})
    assert r.status_code == 422
    assert "Password" in r.json()["detail"]


def test_wrong_password(client):
    register(client)
    r = client.post("/api/auth/login", json={"email": "alice@example.com", "password": "Wrong1234"})
    assert r.status_code == 401


def test_password_is_hashed(client):
    from sqlalchemy import select

    from app.db.session import SessionLocal
    from app.models import User

    register(client)
    with SessionLocal() as db:
        u = db.scalar(select(User))
        assert u.hashed_password != "Passw0rd!" and u.hashed_password.startswith("$2")


def test_protected_route_requires_token(client):
    assert client.get("/api/appliances").status_code == 401
    assert client.get("/api/appliances", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_logout_invalidates_token(client, auth):
    assert client.post("/api/auth/logout", headers=auth).status_code == 200
    assert client.get("/api/auth/me", headers=auth).status_code == 401


def test_forgot_and_reset_password(client):
    register(client)
    r = client.post("/api/auth/forgot-password", json={"email": "alice@example.com"})
    assert r.status_code == 200
    token = r.json()["dev_reset_token"]
    assert token
    # Unknown email returns the same generic message and no token
    r2 = client.post("/api/auth/forgot-password", json={"email": "nobody@example.com"})
    assert r2.json()["message"] == r.json()["message"] and r2.json()["dev_reset_token"] is None

    assert client.post("/api/auth/reset-password", json={"token": "x" * 20, "new_password": "NewPass123"}).status_code == 400
    r = client.post("/api/auth/reset-password", json={"token": token, "new_password": "NewPass123"})
    assert r.status_code == 200
    # Token is single-use
    assert client.post("/api/auth/reset-password", json={"token": token, "new_password": "Other1234"}).status_code == 400
    assert client.post("/api/auth/login", json={"email": "alice@example.com", "password": "NewPass123"}).status_code == 200


def test_profile_update_and_change_password(client, auth):
    r = client.put("/api/users/me", json={"phone": "12345", "household_name": "Home"}, headers=auth)
    assert r.status_code == 200 and r.json()["household_name"] == "Home"
    r = client.post("/api/users/me/change-password", json={"current_password": "bad", "new_password": "Another123"},
                    headers=auth)
    assert r.status_code == 400
    r = client.post("/api/users/me/change-password", json={"current_password": "Passw0rd!", "new_password": "Another123"},
                    headers=auth)
    assert r.status_code == 200
    new = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert client.get("/api/auth/me", headers=auth).status_code == 401  # old token revoked
    assert client.get("/api/auth/me", headers=new).status_code == 200
