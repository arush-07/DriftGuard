def test_register_and_login(client):
    # 1. Register User
    reg_payload = {
        "email": "test_auth@driftguard.io",
        "password": "securepassword123",
        "full_name": "Test Auth User",
        "role": "admin"
    }
    response = client.post("/auth/signup", json=reg_payload)
    assert response.status_code == 201
    assert response.json()["email"] == "test_auth@driftguard.io"
    assert response.json()["role"] == "admin"

    # 2. Login User
    login_payload = {
        "email": "test_auth@driftguard.io",
        "password": "securepassword123"
    }
    response = client.post("/auth/login", json=login_payload)
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["role"] == "admin"

    # 3. Get Me
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "test_auth@driftguard.io"

def test_login_invalid_credentials(client):
    login_payload = {
        "email": "nonexistent@driftguard.io",
        "password": "wrongpassword"
    }
    response = client.post("/auth/login", json=login_payload)
    assert response.status_code == 401
