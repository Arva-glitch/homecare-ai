"""Test fixtures. Uses an isolated SQLite database by default; set TEST_DATABASE_URL to run against MySQL."""
import os
import shutil
import tempfile

TMP = tempfile.mkdtemp(prefix="homecare-test-")
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", f"sqlite:///{TMP}/test.db")
os.environ["UPLOAD_DIR"] = os.path.join(TMP, "uploads")
os.environ["LLM_API_KEY"] = ""  # always exercise the rule-based fallback in tests
os.environ["SMTP_HOST"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.ml.predictor import predictor  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    predictor.force_rules = False
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c
    shutil.rmtree(TMP, ignore_errors=True)


def register(client, email="alice@example.com", password="Passw0rd!", name="Alice Tester"):
    r = client.post("/api/auth/register", json={"full_name": name, "email": email, "password": password})
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture
def auth(client):
    data = register(client)
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest.fixture
def other_auth(client):
    data = register(client, email="bob@example.com", name="Bob Other")
    return {"Authorization": f"Bearer {data['access_token']}"}


APPLIANCE = {
    "name": "Kitchen Fridge",
    "category": "Refrigerator",
    "brand": "LG",
    "model_number": "GL-1",
    "purchase_date": "2018-01-10",
    "installation_date": "2018-01-12",
    "warranty_expiry": "2020-01-10",
    "expected_lifespan_years": 12,
    "last_service_date": "2023-01-01",
    "usage_frequency": "High",
    "condition": "Fair",
}


@pytest.fixture
def appliance(client, auth):
    r = client.post("/api/appliances", json=APPLIANCE, headers=auth)
    assert r.status_code == 201, r.text
    return r.json()
