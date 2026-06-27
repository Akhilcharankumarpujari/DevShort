def test_get_profile_me(client, customer_headers):
    response = client.get("/api/v1/users/me", headers=customer_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "john@example.com"
    assert data["first_name"] == "John"
    assert data["role"] == "customer"

def test_update_profile_me(client, customer_headers):
    response = client.put(
        "/api/v1/users/me",
        headers=customer_headers,
        json={"first_name": "Johnny", "last_name": "Doey"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Johnny"
    assert data["last_name"] == "Doey"
    assert data["email"] == "john@example.com" # unchanged

def test_change_password_me(client, customer_headers):
    # Change password
    response = client.post(
        "/api/v1/users/me/change-password",
        headers=customer_headers,
        json={"old_password": "customerpassword", "new_password": "newcustomerpassword"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Password updated successfully"

    # Login with old password should fail
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "john@example.com", "password": "customerpassword"}
    )
    assert login_resp.status_code == 400

    # Login with new password should succeed
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "john@example.com", "password": "newcustomerpassword"}
    )
    assert login_resp.status_code == 200

def test_soft_delete_me(client, customer_headers):
    # Soft delete account
    response = client.delete("/api/v1/users/me", headers=customer_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Account successfully deactivated"

    # Profile retrieval should now fail with 403 Forbidden because is_active is False
    profile_resp = client.get("/api/v1/users/me", headers=customer_headers)
    assert profile_resp.status_code == 403
    assert "deactivated" in profile_resp.json()["detail"]

    # Login should now fail with 403 Forbidden
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "john@example.com", "password": "customerpassword"}
    )
    assert login_resp.status_code == 403
    assert "deactivated" in login_resp.json()["detail"]

def test_get_all_users_rbac(client, admin_headers, customer_headers):
    # Admin should succeed
    response = client.get("/api/v1/users/", headers=admin_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1

    # Customer should fail with 403 Forbidden
    response = client.get("/api/v1/users/", headers=customer_headers)
    assert response.status_code == 403
    assert "permission" in response.json()["detail"]

def test_get_user_by_id_rbac(client, db, admin_headers, customer_headers):
    # Create another customer directly in DB
    from app.models.user import User
    from app.core.security import hash_password
    other_customer = User(
        first_name="Other",
        last_name="Customer",
        email="other@example.com",
        phone="555",
        password_hash=hash_password("otherpwd"),
        role="customer",
        is_active=True
    )
    db.add(other_customer)
    db.commit()
    db.refresh(other_customer)
    other_id = other_customer.id

    # Admin should be able to get other user's profile
    response = client.get(f"/api/v1/users/{other_id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "other@example.com"

    # Customer should be forbidden from getting other user's profile
    response = client.get(f"/api/v1/users/{other_id}", headers=customer_headers)
    assert response.status_code == 403
    assert "permission" in response.json()["detail"]
