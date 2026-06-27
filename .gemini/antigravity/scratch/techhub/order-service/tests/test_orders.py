import pytest
from unittest.mock import patch

def test_checkout_empty_cart(client, customer_headers):
    response = client.post("/api/v1/orders/checkout", headers=customer_headers)
    assert response.status_code == 400
    assert "cart is empty" in response.json()["detail"]

@patch("app.services.product_service.get_product_metadata")
@patch("app.services.inventory_service.get_inventory_by_product_id")
def test_checkout_insufficient_stock(mock_get_inventory, mock_get_product, client, db, customer_headers):
    from app.models.cart import CartItem
    # Add to cart
    item = CartItem(user_id=2, product_id=101, quantity=5)
    db.add(item)
    db.commit()

    # Mock product metadata
    mock_get_product.return_value = {
        "id": 101,
        "name": "ThinkPad X1 Carbon Gen 11",
        "sku": "LEN-X1-G11",
        "price": 1699.99,
        "discount_percentage": 10.0,
        "is_active": True
    }
    # Mock inventory showing only 2 available
    mock_get_inventory.return_value = {
        "id": 999,
        "product_id": 101,
        "sku": "LEN-X1-G11",
        "available_quantity": 2
    }

    response = client.post("/api/v1/orders/checkout", headers=customer_headers)
    assert response.status_code == 400
    assert "Insufficient stock" in response.json()["detail"]

@patch("app.services.product_service.get_product_metadata")
@patch("app.services.inventory_service.get_inventory_by_product_id")
@patch("app.services.inventory_service.reserve_stock")
def test_checkout_success(mock_reserve, mock_get_inventory, mock_get_product, client, db, customer_headers):
    from app.models.cart import CartItem
    from app.models.order import Order
    
    # Add to cart
    item = CartItem(user_id=2, product_id=101, quantity=2)
    db.add(item)
    db.commit()

    # Mock services
    mock_get_product.return_value = {
        "id": 101,
        "name": "ThinkPad X1 Carbon Gen 11",
        "sku": "LEN-X1-G11",
        "price": 100.00,
        "discount_percentage": 10.0,
        "is_active": True
    }
    mock_get_inventory.return_value = {
        "id": 999,
        "product_id": 101,
        "sku": "LEN-X1-G11",
        "available_quantity": 10
    }
    mock_reserve.return_value = True

    response = client.post("/api/v1/orders/checkout", headers=customer_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "Pending"
    assert data["total_price"] == 180.00 # (100 - 10%) * 2
    assert len(data["items"]) == 1
    assert data["items"][0]["product_name_snapshot"] == "ThinkPad X1 Carbon Gen 11"
    assert data["items"][0]["price_at_purchase"] == 90.00
    assert data["items"][0]["quantity"] == 2

    # Cart should be empty
    items_in_cart = db.query(CartItem).filter(CartItem.user_id == 2).all()
    assert len(items_in_cart) == 0

@patch("app.services.inventory_service.get_inventory_by_product_id")
@patch("app.services.inventory_service.release_stock")
def test_cancel_order_customer(mock_release, mock_get_inventory, client, db, customer_headers):
    from app.models.order import Order, OrderItem
    
    # Create order directly
    order = Order(user_id=2, status="Pending", total_price=100.00)
    db.add(order)
    db.flush()
    
    item = OrderItem(
        order_id=order.id,
        product_id=101,
        quantity=2,
        price_at_purchase=50.00,
        product_name_snapshot="Test",
        product_sku_snapshot="TS"
    )
    db.add(item)
    db.commit()
    db.refresh(order)

    # Mock inventory and release call
    mock_get_inventory.return_value = {"id": 999, "available_quantity": 5}
    mock_release.return_value = True

    response = client.post(f"/api/v1/orders/{order.id}/cancel", headers=customer_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "Cancelled"
    
    # Verify inventory service was called to release stock
    mock_release.assert_called_once_with(999, 2, reason=f"Order {order.id} cancelled/refunded - releasing stock")

def test_cancel_order_invalid_status_customer(client, db, customer_headers):
    from app.models.order import Order
    order = Order(user_id=2, status="Shipped", total_price=100.00)
    db.add(order)
    db.commit()

    response = client.post(f"/api/v1/orders/{order.id}/cancel", headers=customer_headers)
    assert response.status_code == 400
    assert "Cannot cancel" in response.json()["detail"]

@patch("app.services.inventory_service.get_inventory_by_product_id")
@patch("app.services.inventory_service.release_stock")
def test_update_status_admin(mock_release, mock_get_inventory, client, db, admin_headers):
    from app.models.order import Order, OrderItem
    order = Order(user_id=2, status="Pending", total_price=100.00)
    db.add(order)
    db.flush()
    item = OrderItem(order_id=order.id, product_id=101, quantity=2, price_at_purchase=50.00, product_name_snapshot="Test", product_sku_snapshot="TS")
    db.add(item)
    db.commit()
    db.refresh(order)

    response = client.put(
        f"/api/v1/orders/{order.id}/status",
        headers=admin_headers,
        json={"status": "Processing", "notes": "Fulfillment started"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Processing"

    # Transition to Cancelled through admin status update
    mock_get_inventory.return_value = {"id": 999}
    mock_release.return_value = True
    
    response = client.put(
        f"/api/v1/orders/{order.id}/status",
        headers=admin_headers,
        json={"status": "Cancelled", "notes": "Customer request"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Cancelled"
    mock_release.assert_called_once()

@patch("app.services.inventory_service.get_inventory_by_product_id")
@patch("app.services.inventory_service.release_stock")
def test_refund_order_admin(mock_release, mock_get_inventory, client, db, admin_headers):
    from app.models.order import Order, OrderItem
    order = Order(user_id=2, status="Confirmed", total_price=100.00)
    db.add(order)
    db.flush()
    item = OrderItem(order_id=order.id, product_id=101, quantity=2, price_at_purchase=50.00, product_name_snapshot="Test", product_sku_snapshot="TS")
    db.add(item)
    db.commit()
    db.refresh(order)

    mock_get_inventory.return_value = {"id": 999}
    mock_release.return_value = True

    response = client.post(f"/api/v1/orders/{order.id}/refund", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "Refunded"
    mock_release.assert_called_once()

def test_soft_delete_order_admin(client, db, admin_headers):
    from app.models.order import Order
    order = Order(user_id=2, status="Cancelled", total_price=100.00, is_active=True)
    db.add(order)
    db.commit()

    response = client.delete(f"/api/v1/orders/{order.id}", headers=admin_headers)
    assert response.status_code == 200
    assert "soft-deleted" in response.json()["message"]

    db_order = db.query(Order).filter(Order.id == order.id).first()
    assert db_order.is_active is False
