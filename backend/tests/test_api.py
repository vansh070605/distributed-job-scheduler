import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.api.deps import get_db
from app.db.base_class import Base

# Setup in-memory SQLite for fast sync test runs
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def run_around_tests():
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables
    Base.metadata.drop_all(bind=engine)


def test_health_check_endpoint():
    response = client.get("/monitoring/liveness")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_auth_registration():
    payload = {
        "email": "test-developer@scheduler.io",
        "password": "securepassword",
        "full_name": "Test Developer",
        "role": "admin"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test-developer@scheduler.io"
    assert "id" in data


def test_auth_login():
    # Register first
    payload = {
        "email": "login-test@scheduler.io",
        "password": "testpassword",
        "full_name": "Login Tester",
        "role": "viewer"
    }
    client.post("/api/v1/auth/register", json=payload)

    # Login
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "login-test@scheduler.io", "password": "testpassword"},
    )
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
