import pytest

def test_add_item_to_cart(client, customer_headers):
    response = client.post(
        "/api/v1/cart/",
        headers=customer_headers,
        json={"product_id": 101, "quantity": 2}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["product_id"] == 101
    assert data["quantity"] == 2
    assert data["user_id"] == 2 # from token
    assert "id" in data

    # Add duplicate product_id to increment quantity
    response = client.post(
        "/api/v1/cart/",
        headers=customer_headers,
        json={"product_id": 101, "quantity": 3}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["quantity"] == 5

def test_view_cart(client, db, customer_headers):
    from app.models.cart import CartItem
    item1 = CartItem(user_id=2, product_id=101, quantity=2)
    item2 = CartItem(user_id=2, product_id=102, quantity=1)
    item3 = CartItem(user_id=3, product_id=101, quantity=5) # other user
    db.add_all([item1, item2, item3])
    db.commit()

    response = client.get("/api/v1/cart/", headers=customer_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    product_ids = [item["product_id"] for item in data]
    assert 101 in product_ids
    assert 102 in product_ids

def test_update_cart_item_quantity(client, db, customer_headers):
    from app.models.cart import CartItem
    item = CartItem(user_id=2, product_id=101, quantity=2)
    db.add(item)
    db.commit()
    db.refresh(item)

    response = client.put(
        f"/api/v1/cart/{item.id}",
        headers=customer_headers,
        json={"quantity": 10}
    )
    assert response.status_code == 200
    assert response.json()["quantity"] == 10

    # Try to update another user's cart item
    other_item = CartItem(user_id=3, product_id=102, quantity=1)
    db.add(other_item)
    db.commit()
    db.refresh(other_item)

    response = client.put(
        f"/api/v1/cart/{other_item.id}",
        headers=customer_headers,
        json={"quantity": 5}
    )
    assert response.status_code == 404

def test_remove_item_from_cart(client, db, customer_headers):
    from app.models.cart import CartItem
    item = CartItem(user_id=2, product_id=101, quantity=2)
    db.add(item)
    db.commit()
    db.refresh(item)

    response = client.delete(f"/api/v1/cart/{item.id}", headers=customer_headers)
    assert response.status_code == 200
    assert "removed" in response.json()["message"]

    db_item = db.query(CartItem).filter(CartItem.id == item.id).first()
    assert db_item is None

def test_clear_cart(client, db, customer_headers):
    from app.models.cart import CartItem
    item1 = CartItem(user_id=2, product_id=101, quantity=2)
    item2 = CartItem(user_id=2, product_id=102, quantity=1)
    db.add_all([item1, item2])
    db.commit()

    response = client.delete("/api/v1/cart/", headers=customer_headers)
    assert response.status_code == 200
    assert "cleared" in response.json()["message"]

    cart_items = db.query(CartItem).filter(CartItem.user_id == 2).all()
    assert len(cart_items) == 0

def test_cart_access_unauthorized(client):
    response = client.get("/api/v1/cart/")
    assert response.status_code == 401
