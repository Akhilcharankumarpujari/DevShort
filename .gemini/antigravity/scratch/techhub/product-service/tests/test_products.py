import pytest

def test_create_product_admin(client, admin_headers):
    response = client.post(
        "/api/v1/products/",
        headers=admin_headers,
        json={
            "name": "ThinkPad X1 Carbon Gen 11",
            "description": "High-end business laptop",
            "brand": "Lenovo",
            "category": "Laptops",
            "sku": "LEN-X1-G11",
            "price": 1699.99,
            "discount_percentage": 10.0,
            "stock_quantity": 25,
            "image_urls": ["http://example.com/x1.jpg"]
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "ThinkPad X1 Carbon Gen 11"
    assert data["sku"] == "LEN-X1-G11"
    assert data["average_rating"] == 0.0
    assert data["review_count"] == 0
    assert data["is_active"] is True
    assert "id" in data

    # Test duplicate SKU
    response = client.post(
        "/api/v1/products/",
        headers=admin_headers,
        json={
            "name": "Another Lenovo Laptop",
            "brand": "Lenovo",
            "category": "Laptops",
            "sku": "LEN-X1-G11",
            "price": 1200.00
        }
    )
    assert response.status_code == 400
    assert "SKU already exists" in response.json()["detail"]

def test_create_product_customer(client, customer_headers):
    response = client.post(
        "/api/v1/products/",
        headers=customer_headers,
        json={
            "name": "MacBook Pro 16",
            "brand": "Apple",
            "category": "Laptops",
            "sku": "APP-MBP-16",
            "price": 2499.99
        }
    )
    assert response.status_code == 403
    assert "permission" in response.json()["detail"]

def test_create_product_anonymous(client):
    response = client.post(
        "/api/v1/products/",
        json={
            "name": "MacBook Pro 16",
            "brand": "Apple",
            "category": "Laptops",
            "sku": "APP-MBP-16",
            "price": 2499.99
        }
    )
    assert response.status_code == 401

def test_get_product_by_id(client, db):
    # Create product directly in db
    from app.models.product import Product
    prod = Product(
        name="Keychron Q3 Pro",
        brand="Keychron",
        category="Keyboards",
        sku="KEY-Q3-PRO",
        price=189.99,
        is_active=True
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)

    response = client.get(f"/api/v1/products/{prod.id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Keychron Q3 Pro"
    assert response.json()["sku"] == "KEY-Q3-PRO"

    # Get non-existent
    response = client.get("/api/v1/products/99999")
    assert response.status_code == 404

def test_update_product_admin(client, db, admin_headers):
    from app.models.product import Product
    prod = Product(
        name="G502 Hero Mouse",
        brand="Logitech",
        category="Mice",
        sku="LOG-G502-HERO",
        price=79.99,
        is_active=True
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)

    response = client.put(
        f"/api/v1/products/{prod.id}",
        headers=admin_headers,
        json={
            "name": "G502 LightSpeed Wireless",
            "price": 149.99,
            "stock_quantity": 50
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "G502 LightSpeed Wireless"
    assert data["price"] == 149.99
    assert data["stock_quantity"] == 50
    assert data["brand"] == "Logitech" # unchanged

def test_update_product_customer(client, db, customer_headers):
    from app.models.product import Product
    prod = Product(
        name="MX Master 3S",
        brand="Logitech",
        category="Mice",
        sku="LOG-MXM-3S",
        price=99.99,
        is_active=True
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)

    response = client.put(
        f"/api/v1/products/{prod.id}",
        headers=customer_headers,
        json={"price": 89.99}
    )
    assert response.status_code == 403

def test_delete_product_admin(client, db, admin_headers):
    from app.models.product import Product
    prod = Product(
        name="RTX 4090 GPU",
        brand="NVIDIA",
        category="GPUs",
        sku="NV-RTX-4090",
        price=1599.99,
        is_active=True
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)

    response = client.delete(f"/api/v1/products/{prod.id}", headers=admin_headers)
    assert response.status_code == 200
    assert "success" in response.json()["message"]

    # Product should now be soft deleted (is_active = False)
    db.refresh(prod)
    assert prod.is_active is False

    # Get product by ID should now return 404
    get_resp = client.get(f"/api/v1/products/{prod.id}")
    assert get_resp.status_code == 404

def test_delete_product_customer(client, db, customer_headers):
    from app.models.product import Product
    prod = Product(
        name="RTX 4080 Super",
        brand="NVIDIA",
        category="GPUs",
        sku="NV-RTX-4080-S",
        price=999.99,
        is_active=True
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)

    response = client.delete(f"/api/v1/products/{prod.id}", headers=customer_headers)
    assert response.status_code == 403

def test_list_products_filtering_and_sorting(client, db):
    from app.models.product import Product
    p1 = Product(name="Intel Core i9-14900K", brand="Intel", category="CPUs", sku="INT-I9-14900K", price=589.99, average_rating=4.8, is_active=True)
    p2 = Product(name="AMD Ryzen 7 7800X3D", brand="AMD", category="CPUs", sku="AMD-R7-7800X3D", price=369.99, average_rating=4.9, is_active=True)
    p3 = Product(name="Corsair Vengeance 32GB RAM", brand="Corsair", category="Memory", sku="COR-VEN-32", price=119.99, average_rating=4.5, is_active=True)
    p4 = Product(name="Samsung 990 Pro 2TB SSD", brand="Samsung", category="Storage", sku="SAM-990-2TB", price=169.99, average_rating=4.7, is_active=True)
    p5 = Product(name="Inactive CPU", brand="Intel", category="CPUs", sku="INT-INACTIVE", price=100.00, average_rating=1.0, is_active=False)
    
    db.add_all([p1, p2, p3, p4, p5])
    db.commit()

    # 1. List active only
    response = client.get("/api/v1/products/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 4
    assert len(data["items"]) == 4

    # 2. Search query test
    response = client.get("/api/v1/products/?q=Ryzen")
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["sku"] == "AMD-R7-7800X3D"

    # 3. Category filter test
    response = client.get("/api/v1/products/?category=CPUs")
    assert response.json()["total"] == 2
    skus = [item["sku"] for item in response.json()["items"]]
    assert "INT-I9-14900K" in skus
    assert "AMD-R7-7800X3D" in skus

    # 4. Brand filter test
    response = client.get("/api/v1/products/?brand=Corsair")
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["brand"] == "Corsair"

    # 5. Price range filter test
    response = client.get("/api/v1/products/?min_price=150&max_price=400")
    assert response.json()["total"] == 2 # Ryzen (369.99) and Samsung SSD (169.99)
    skus = [item["sku"] for item in response.json()["items"]]
    assert "AMD-R7-7800X3D" in skus
    assert "SAM-990-2TB" in skus

    # 6. Sorting by price asc
    response = client.get("/api/v1/products/?sort_by=price_asc")
    prices = [item["price"] for item in response.json()["items"]]
    assert prices == [119.99, 169.99, 369.99, 589.99]

    # 7. Sorting by price desc
    response = client.get("/api/v1/products/?sort_by=price_desc")
    prices = [item["price"] for item in response.json()["items"]]
    assert prices == [589.99, 369.99, 169.99, 119.99]

    # 8. Sorting by rating desc
    response = client.get("/api/v1/products/?sort_by=rating")
    ratings = [item["average_rating"] for item in response.json()["items"]]
    assert ratings == [4.9, 4.8, 4.7, 4.5]

    # 9. Pagination
    response = client.get("/api/v1/products/?skip=1&limit=2")
    assert len(response.json()["items"]) == 2
    assert response.json()["total"] == 4
