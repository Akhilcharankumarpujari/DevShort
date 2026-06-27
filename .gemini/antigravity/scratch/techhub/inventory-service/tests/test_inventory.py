import pytest

def test_create_inventory_admin(client, admin_headers):
    response = client.post(
        "/api/v1/inventory/",
        headers=admin_headers,
        json={
            "product_id": 101,
            "warehouse_id": "Warehouse-A",
            "sku": "LEN-X1-G11",
            "low_stock_threshold": 5,
            "initial_quantity": 20
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["product_id"] == 101
    assert data["warehouse_id"] == "Warehouse-A"
    assert data["sku"] == "LEN-X1-G11"
    assert data["available_quantity"] == 20
    assert data["reserved_quantity"] == 0
    assert data["status"] == "IN_STOCK"
    assert "id" in data

    # Test duplicate product_id or sku
    response = client.post(
        "/api/v1/inventory/",
        headers=admin_headers,
        json={
            "product_id": 101,
            "warehouse_id": "Warehouse-B",
            "sku": "LEN-X1-G11",
            "low_stock_threshold": 5,
            "initial_quantity": 10
        }
    )
    assert response.status_code == 400

def test_create_inventory_customer(client, customer_headers):
    response = client.post(
        "/api/v1/inventory/",
        headers=customer_headers,
        json={
            "product_id": 102,
            "warehouse_id": "Warehouse-A",
            "sku": "APP-MBP-16",
            "low_stock_threshold": 5,
            "initial_quantity": 10
        }
    )
    assert response.status_code == 403

def test_get_inventory_by_id_and_product_id(client, db, admin_headers):
    from app.models.inventory import Inventory
    inv = Inventory(
        product_id=201,
        warehouse_id="Warehouse-A",
        sku="KEY-Q3-PRO",
        available_quantity=15,
        reserved_quantity=0,
        low_stock_threshold=5,
        status="IN_STOCK"
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)

    response = client.get(f"/api/v1/inventory/{inv.id}")
    assert response.status_code == 200
    assert response.json()["sku"] == "KEY-Q3-PRO"

    response = client.get(f"/api/v1/inventory/product/201")
    assert response.status_code == 200
    assert response.json()["id"] == inv.id

    response = client.get("/api/v1/inventory/99999")
    assert response.status_code == 404

def test_update_inventory_admin(client, db, admin_headers):
    from app.models.inventory import Inventory
    inv = Inventory(
        product_id=202,
        warehouse_id="Warehouse-A",
        sku="LOG-MXM-3S",
        available_quantity=6,
        reserved_quantity=0,
        low_stock_threshold=5,
        status="IN_STOCK"
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)

    response = client.put(
        f"/api/v1/inventory/{inv.id}",
        headers=admin_headers,
        json={
            "warehouse_id": "Warehouse-B",
            "low_stock_threshold": 8
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["warehouse_id"] == "Warehouse-B"
    assert data["low_stock_threshold"] == 8
    # Since quantity (6) <= threshold (8), status should become LOW_STOCK
    assert data["status"] == "LOW_STOCK"

def test_increase_stock_admin(client, db, admin_headers):
    from app.models.inventory import Inventory
    inv = Inventory(
        product_id=203,
        warehouse_id="Warehouse-A",
        sku="RTX-4080",
        available_quantity=2,
        reserved_quantity=0,
        low_stock_threshold=5,
        status="LOW_STOCK"
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)

    response = client.post(
        f"/api/v1/inventory/{inv.id}/increase",
        headers=admin_headers,
        json={"amount": 10, "reason": "Restock"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["available_quantity"] == 12
    assert data["status"] == "IN_STOCK"

def test_decrease_stock_admin(client, db, admin_headers):
    from app.models.inventory import Inventory
    inv = Inventory(
        product_id=204,
        warehouse_id="Warehouse-A",
        sku="RTX-4090",
        available_quantity=12,
        reserved_quantity=0,
        low_stock_threshold=5,
        status="IN_STOCK"
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)

    response = client.post(
        f"/api/v1/inventory/{inv.id}/decrease",
        headers=admin_headers,
        json={"amount": 10, "reason": "Direct sale"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["available_quantity"] == 2
    assert data["status"] == "LOW_STOCK"

    # Decrease below 0 should fail
    response = client.post(
        f"/api/v1/inventory/{inv.id}/decrease",
        headers=admin_headers,
        json={"amount": 5}
    )
    assert response.status_code == 400

def test_reserve_stock(client, db):
    from app.models.inventory import Inventory
    inv = Inventory(
        product_id=205,
        warehouse_id="Warehouse-A",
        sku="SAM-990-1TB",
        available_quantity=10,
        reserved_quantity=2,
        low_stock_threshold=5,
        status="IN_STOCK"
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)

    response = client.post(
        f"/api/v1/inventory/{inv.id}/reserve",
        json={"amount": 6, "reason": "Checkout #123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["available_quantity"] == 4
    assert data["reserved_quantity"] == 8
    assert data["status"] == "LOW_STOCK"

    # Reserve too much
    response = client.post(
        f"/api/v1/inventory/{inv.id}/reserve",
        json={"amount": 5}
    )
    assert response.status_code == 400

def test_release_stock(client, db):
    from app.models.inventory import Inventory
    inv = Inventory(
        product_id=206,
        warehouse_id="Warehouse-A",
        sku="SAM-990-2TB",
        available_quantity=4,
        reserved_quantity=8,
        low_stock_threshold=5,
        status="LOW_STOCK"
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)

    response = client.post(
        f"/api/v1/inventory/{inv.id}/release",
        json={"amount": 3, "reason": "Order cancelled"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["available_quantity"] == 7
    assert data["reserved_quantity"] == 5
    assert data["status"] == "IN_STOCK"

    # Release too much
    response = client.post(
        f"/api/v1/inventory/{inv.id}/release",
        json={"amount": 10}
    )
    assert response.status_code == 400

def test_get_history(client, db, admin_headers):
    from app.models.inventory import Inventory
    inv = Inventory(
        product_id=207,
        warehouse_id="Warehouse-A",
        sku="COR-VEN-64",
        available_quantity=10,
        reserved_quantity=0,
        low_stock_threshold=5,
        status="IN_STOCK"
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)

    # Perform increase
    client.post(
        f"/api/v1/inventory/{inv.id}/increase",
        headers=admin_headers,
        json={"amount": 5, "reason": "Restock"}
    )

    # Perform reserve
    client.post(
        f"/api/v1/inventory/{inv.id}/reserve",
        json={"amount": 3, "reason": "Hold"}
    )

    # Get history
    response = client.get(f"/api/v1/inventory/{inv.id}/history")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 2
    assert history[0]["action"] == "RESERVE"
    assert history[0]["quantity_changed"] == 3
    assert history[0]["old_available"] == 15
    assert history[0]["new_available"] == 12
    assert history[0]["old_reserved"] == 0
    assert history[0]["new_reserved"] == 3

    assert history[1]["action"] == "INCREASE"
    assert history[1]["quantity_changed"] == 5

def test_low_stock_and_out_of_stock_lists(client, db):
    from app.models.inventory import Inventory
    i1 = Inventory(product_id=301, warehouse_id="W", sku="SKU1", available_quantity=15, reserved_quantity=0, low_stock_threshold=5, status="IN_STOCK")
    i2 = Inventory(product_id=302, warehouse_id="W", sku="SKU2", available_quantity=3, reserved_quantity=0, low_stock_threshold=5, status="LOW_STOCK")
    i3 = Inventory(product_id=303, warehouse_id="W", sku="SKU3", available_quantity=0, reserved_quantity=0, low_stock_threshold=5, status="OUT_OF_STOCK")
    db.add_all([i1, i2, i3])
    db.commit()

    # Low Stock
    response = client.get("/api/v1/inventory/status/low-stock")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["product_id"] == 302

    # Out of Stock
    response = client.get("/api/v1/inventory/status/out-of-stock")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["product_id"] == 303
