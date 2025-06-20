from operator import is_
import os
import secrets
import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient
from app.main import app

local_mongodb_uri = "mongodb://admin:admin@localhost:30017/"
ci_mongodb_uri = os.getenv("MONGODB_URI")

is_ci = os.getenv("CI", "false").lower() == "true"

mongodb_test_uri = ci_mongodb_uri if is_ci else local_mongodb_uri
mongodb_test_db = "test_db"


@pytest.fixture
def set_test_env(monkeypatch):
    """Set environment variables for testing."""
    monkeypatch.setenv("MONGODB_URI", mongodb_test_uri)
    monkeypatch.setenv("MONGODB_NAME", mongodb_test_db)
    monkeypatch.setenv("PK_ENV", "test")


@pytest.fixture(autouse=True)
def client(set_test_env):
    """Create a TestClient for the FastAPI app and provide it to the tests as context."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def user_email():
    """Generate a random email address for testing."""
    rand = secrets.token_hex(8)
    return f"test-{rand}@example.com"


@pytest.fixture
def login_user(client, user_email):
    """Helper fixture to log in a user and return their token, id, and email."""
    response = client.post(
        "/auth/instant-login-code",
        json={"email": user_email},
    )
    assert response.status_code == 201
    data = response.json()

    response = client.post(
        "/auth/verify-login-code",
        json={"email": user_email, "loginCode": data["loginCode"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "id" in data
    assert "email" in data
    return data["token"], data["id"], data["email"]


def pytest_sessionfinish(session, exitstatus):
    print("\nCleaning up test environment...")
    try:
        client = MongoClient(mongodb_test_uri)
        client.drop_database(mongodb_test_db)
        client.close()
        print(f"Dropped test database: {mongodb_test_db}")
    except Exception as e:
        print(f"Error dropping test database: {e}")
