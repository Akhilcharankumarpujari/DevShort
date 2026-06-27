import pytest
from unittest.mock import patch

def test_create_payment_intent(client, customer_headers):
    response = client.post(
        "/api/v1/payments/",
        headers=customer_headers,
        json={
            "order_id": 5001,
            "payment_method": "CREDIT_CARD",
            "amount": 199.99,
            "currency": "USD",
            "idempotency_key": "idemp-key-123456"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["order_id"] == 5001
    assert data["payment_method"] == "CREDIT_CARD"
    assert data["amount"] == 199.99
    assert data["status"] == "PENDING"
    assert "id" in data

    # Idempotency check: sending duplicate key returns same response
    response_dup = client.post(
        "/api/v1/payments/",
        headers=customer_headers,
        json={
            "order_id": 5001,
            "payment_method": "CREDIT_CARD",
            "amount": 199.99,
            "currency": "USD",
            "idempotency_key": "idemp-key-123456"
        }
    )
    assert response_dup.status_code == 201
    assert response_dup.json()["id"] == data["id"]

@patch("app.services.order_service.confirm_order")
def test_confirm_payment_success(mock_confirm_order, client, db, customer_headers):
    from app.models.payment import Payment
    payment = Payment(
        order_id=5002,
        user_id=2,
        payment_method="PAYPAL",
        amount=50.00,
        currency="USD",
        idempotency_key="idemp-key-777",
        status="PENDING"
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    # Mock order confirmation callback
    mock_confirm_order.return_value = True

    response = client.post(
        f"/api/v1/payments/{payment.id}/confirm",
        headers=customer_headers,
        json={"simulate_success": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["transaction_id"] is not None
    
    mock_confirm_order.assert_called_once_with(5002)

def test_confirm_payment_failure(client, db, customer_headers):
    from app.models.payment import Payment
    payment = Payment(
        order_id=5003,
        user_id=2,
        payment_method="PAYPAL",
        amount=50.00,
        currency="USD",
        idempotency_key="idemp-key-888",
        status="PENDING"
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    response = client.post(
        f"/api/v1/payments/{payment.id}/confirm",
        headers=customer_headers,
        json={"simulate_success": False}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "FAILED"

def test_get_payment_details_rbac(client, db, customer_headers, admin_headers):
    from app.models.payment import Payment
    p1 = Payment(order_id=5004, user_id=2, payment_method="CC", amount=10.0, idempotency_key="k1", status="PENDING")
    p2 = Payment(order_id=5005, user_id=3, payment_method="CC", amount=20.0, idempotency_key="k2", status="PENDING") # other customer
    db.add_all([p1, p2])
    db.commit()
    db.refresh(p1)
    db.refresh(p2)

    # Customer viewing own: success
    resp = client.get(f"/api/v1/payments/{p1.id}", headers=customer_headers)
    assert resp.status_code == 200

    # Customer viewing other's: forbidden
    resp = client.get(f"/api/v1/payments/{p2.id}", headers=customer_headers)
    assert resp.status_code == 403

    # Admin viewing other's: success
    resp = client.get(f"/api/v1/payments/{p2.id}", headers=admin_headers)
    assert resp.status_code == 200

def test_refund_payment_admin(client, db, admin_headers):
    from app.models.payment import Payment
    p_success = Payment(order_id=5006, user_id=2, payment_method="CC", amount=100.0, idempotency_key="k-succ", status="SUCCESS")
    p_pending = Payment(order_id=5007, user_id=2, payment_method="CC", amount=100.0, idempotency_key="k-pend", status="PENDING")
    db.add_all([p_success, p_pending])
    db.commit()
    db.refresh(p_success)
    db.refresh(p_pending)

    # Refund success: ok
    resp = client.post(f"/api/v1/payments/{p_success.id}/refund", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "REFUNDED"

    # Refund pending: fail
    resp = client.post(f"/api/v1/payments/{p_pending.id}/refund", headers=admin_headers)
    assert resp.status_code == 400
    assert "Cannot refund" in resp.json()["detail"]

def test_list_payments_rbac(client, db, customer_headers, admin_headers):
    from app.models.payment import Payment
    p1 = Payment(order_id=5008, user_id=2, payment_method="CC", amount=10.0, idempotency_key="k8", status="PENDING")
    p2 = Payment(order_id=5009, user_id=3, payment_method="CC", amount=20.0, idempotency_key="k9", status="PENDING")
    db.add_all([p1, p2])
    db.commit()

    # Customer sees 1
    resp = client.get("/api/v1/payments/", headers=customer_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # Admin sees 2
    resp = client.get("/api/v1/payments/", headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2

def test_payment_history(client, db, customer_headers):
    # Create intent via API to initialize history
    resp_create = client.post(
        "/api/v1/payments/",
        headers=customer_headers,
        json={
            "order_id": 5010,
            "payment_method": "CC",
            "amount": 10.0,
            "currency": "USD",
            "idempotency_key": "k10-history-key"
        }
    )
    assert resp_create.status_code == 201
    payment_id = resp_create.json()["id"]

    # Confirm to trigger status change
    client.post(
        f"/api/v1/payments/{payment_id}/confirm",
        headers=customer_headers,
        json={"simulate_success": True}
    )

    resp = client.get(f"/api/v1/payments/{payment_id}/history", headers=customer_headers)
    assert resp.status_code == 200
    history = resp.json()
    assert len(history) == 2
    assert history[0]["status"] == "SUCCESS"
    assert history[1]["status"] == "PENDING"
