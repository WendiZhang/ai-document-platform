import os

os.environ["APP_ENV"] = "test"

os.environ[
    "DATABASE_URL"
] = (
    "postgresql+psycopg://"
    "document_user:document_password"
    "@localhost:5432/"
    "document_intelligence_test"
)

os.environ[
    "JWT_SECRET_KEY"
] = "test_secret_key_for_pytest"

os.environ[
    "OPENAI_API_KEY"
] = "test-key"

os.environ[
    "UPLOAD_DIRECTORY"
] = "test_uploads"


import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.models import (
    ChatMessage,
    ChatSession,
    Document,
    DocumentChunk,
    User,
)


TEST_DATABASE_URL = os.environ[
    "DATABASE_URL"
]


test_engine = create_engine(
    TEST_DATABASE_URL,
)


TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(
    scope="session",
    autouse=True,
)
def setup_test_database():
    with test_engine.begin() as connection:
        connection.execute(
            text(
                "CREATE EXTENSION "
                "IF NOT EXISTS vector"
            )
        )

    Base.metadata.drop_all(
        bind=test_engine,
    )

    Base.metadata.create_all(
        bind=test_engine,
    )

    yield

    Base.metadata.drop_all(
        bind=test_engine,
    )


@pytest.fixture()
def db():
    connection = test_engine.connect()

    transaction = connection.begin()

    session = TestingSessionLocal(
        bind=connection,
    )

    try:
        yield session

    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = (
        override_get_db
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    
@pytest.fixture()
def auth_headers(client):
    user_data = {
        "name": "Pytest User",
        "email": "pytest@example.com",
        "password": "Password123!",
    }

    register_response = client.post(
        "/api/auth/register",
        json=user_data,
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        data={
            "username": user_data["email"],
            "password": user_data["password"],
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }
