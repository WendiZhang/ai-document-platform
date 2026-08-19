def test_register_user(client):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "Password123!",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == (
        "test@example.com"
    )
    
def test_register_duplicate_email(client):
    user_data = {
        "name": "Test User",
        "email": "duplicate@example.com",
        "password": "Password123!",
    }

    first_response = client.post(
        "/api/auth/register",
        json=user_data,
    )

    assert first_response.status_code in {
        200,
        201,
    }

    second_response = client.post(
        "/api/auth/register",
        json=user_data,
    )

    assert second_response.status_code in {
        400,
        409,
    }
    
def test_login_user(client):
    user_data = {
        "name": "Login User",
        "email": "login@example.com",
        "password": "Password123!",
    }

    client.post(
        "/api/auth/register",
        json=user_data,
    )

    response = client.post(
        "/api/auth/login",
        data={
            "username": "login@example.com",
            "password": "Password123!",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
