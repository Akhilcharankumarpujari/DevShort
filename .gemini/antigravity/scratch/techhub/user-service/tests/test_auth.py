def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
            "phone": "555-0199",
            "password": "supersecurepassword",
            "role": "customer"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert data["first_name"] == "Alice"
    assert "id" in data
    assert "password_hash" not in data

    # Test duplicate email registration
    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Alice2",
            "last_name": "Smith2",
            "email": "alice@example.com",
            "phone": "555-0200",
            "password": "anotherpassword",
            "role": "customer"
        }
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_login_user(client, db):
    # Register first
    client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Bob",
            "last_name": "Jones",
            "email": "bob@example.com",
            "password": "bobpassword",
            "role": "customer"
        }
    )
    
    # Login success
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "bobpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    # Login failure - wrong password
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 400
    assert "Incorrect email or password" in response.json()["detail"]

def test_logout_user(client, db):
    # Register and login
    client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Charlie",
            "last_name": "Brown",
            "email": "charlie@example.com",
            "password": "charliepwd",
            "role": "customer"
        }
    )
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "charlie@example.com", "password": "charliepwd"}
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify profile works with token
    profile_resp = client.get("/api/v1/users/me", headers=headers)
    assert profile_resp.status_code == 200

    # Logout
    logout_resp = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_resp.status_code == 200
    assert logout_resp.json()["message"] == "Successfully logged out"

    # Verify profile fails now
    profile_resp = client.get("/api/v1/users/me", headers=headers)
    assert profile_resp.status_code == 401
    assert "logged out" in profile_resp.json()["detail"]

def test_refresh_token(client, db):
    client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Delta",
            "last_name": "Force",
            "email": "delta@example.com",
            "password": "deltapassword",
            "role": "customer"
        }
    )
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "delta@example.com", "password": "deltapassword"}
    )
    refresh_token = login_resp.json()["refresh_token"]

    # Refresh
    refresh_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert refresh_resp.status_code == 200
    data = refresh_resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
