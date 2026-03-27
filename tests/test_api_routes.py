import json
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.cache import redis_client
from app.database import get_db as get_db_dependency
from app.main import app as fastapi_app
from app.models import Product, Coupon, Order


@pytest.fixture()
def client(db_session):
    """
    TestClient + override de la dépendance get_db pour utiliser la DB en mémoire fournie par conftest.
    """

    def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db_dependency] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


def test_health_and_root(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    r = client.get("/")
    assert r.status_code == 200
    assert "message" in r.json()


def test_products_crud_and_cache(client, db_session):
    # Cache miss : redis_client.get doit renvoyer None
    redis_client.get.return_value = None

    # Create
    payload = {"name": "Laptop Pro", "price": 999.99, "stock": 10, "category": "informatique", "description": "X"}
    r = client.post("/products/", json=payload)
    assert r.status_code == 201
    product_id = r.json()["id"]

    # List (doit inclure le produit créé)
    r = client.get("/products/")
    assert r.status_code == 200
    assert any(p["id"] == product_id for p in r.json())

    # Get - cache miss => set_cached appelé
    redis_client.get.return_value = None
    r = client.get(f"/products/{product_id}")
    assert r.status_code == 200
    assert r.json()["id"] == product_id
    redis_client.set.assert_called()  # couvre set_cached()

    # Get - cache hit => json.loads(cached)
    created_at = (datetime.utcnow() - timedelta(days=1)).replace(microsecond=0).isoformat()
    redis_client.get.return_value = json.dumps(
        {
            "id": product_id,
            "name": "Laptop Pro",
            "price": 999.99,
            "stock": 10,
            "category": "informatique",
            "description": "X",
            "active": True,
            "created_at": created_at,
        }
    )
    r = client.get(f"/products/{product_id}")
    assert r.status_code == 200
    assert r.json()["id"] == product_id

    # Not found
    redis_client.get.return_value = None
    r = client.get("/products/999999")
    assert r.status_code == 404

    # Update - couvre delete_cached()
    redis_client.delete.reset_mock()
    r = client.put(f"/products/{product_id}", json={"price": 123.45, "stock": 5})
    assert r.status_code == 200
    assert r.json()["price"] == 123.45
    assert r.json()["stock"] == 5
    redis_client.delete.assert_called()  # couvre delete_cached()

    # Delete
    r = client.delete(f"/products/{product_id}")
    assert r.status_code == 204

    # Vérifie que le produit n'est plus listé (active=False)
    r = client.get("/products/")
    assert r.status_code == 200
    assert all(p["id"] != product_id for p in r.json())


def test_cart_lifecycle_success_and_errors(client, db_session, product_sample):
    user_id = 42
    product_id = product_sample.id

    # Clear cart non-existant => 404
    r = client.delete(f"/cart/{user_id}")
    assert r.status_code == 404

    # Add to cart
    r = client.post(f"/cart/?user_id={user_id}", json={"product_id": product_id, "quantity": 2})
    assert r.status_code == 201
    body = r.json()
    assert body["id"] is not None
    assert body["user_id"] == user_id
    assert body["items"][0]["product_id"] == product_id
    assert body["items"][0]["quantity"] == 2
    assert body["sous_total"] > 0

    # View cart
    r = client.get(f"/cart/{user_id}")
    assert r.status_code == 200
    assert len(r.json()["items"]) == 1

    # Remove item
    r = client.delete(f"/cart/{user_id}/item/{product_id}")
    assert r.status_code == 200
    assert r.json()["items"] == []

    # Create empty cart then remove non-existing item => 404 (ValueError -> HTTPException)
    r = client.get(f"/cart/{user_id}")
    assert r.status_code == 200
    r = client.delete(f"/cart/{user_id}/item/{product_id}")
    assert r.status_code == 404

    # Add again then clear cart => 204 + panier vide
    r = client.post(f"/cart/?user_id={user_id}", json={"product_id": product_id, "quantity": 1})
    assert r.status_code == 201
    r = client.delete(f"/cart/{user_id}")
    assert r.status_code == 204
    r = client.get(f"/cart/{user_id}")
    assert r.status_code == 200
    assert r.json()["items"] == []


def test_orders_success_coupon_and_stock_failure(client, db_session, product_sample, coupon_sample):
    user_id = 42

    # Create cart
    product_id = product_sample.id
    r = client.post(f"/cart/?user_id={user_id}", json={"product_id": product_id, "quantity": 2})
    assert r.status_code == 201

    # Order without coupon
    r = client.post("/orders/", json={"user_id": user_id})
    assert r.status_code == 201
    order = r.json()
    assert order["status"] == "pending"
    assert order["user_id"] == user_id
    assert len(order["items"]) == 1

    # Cart should be emptied
    r = client.get(f"/cart/{user_id}")
    assert r.status_code == 200
    assert r.json()["items"] == []

    # Add again then order with coupon
    r = client.post(f"/cart/?user_id={user_id}", json={"product_id": product_id, "quantity": 2})
    assert r.status_code == 201
    r = client.post("/orders/", json={"user_id": user_id, "coupon_code": coupon_sample.code})
    assert r.status_code == 201
    order_with_coupon = r.json()
    assert order_with_coupon["coupon_code"] == coupon_sample.code

    # Stock insuffisant => 400
    low_stock_product = Product(name="Low stock", price=10.0, stock=1, active=True)
    db_session.add(low_stock_product)
    db_session.commit()
    db_session.refresh(low_stock_product)

    r = client.post(f"/cart/?user_id={user_id}", json={"product_id": low_stock_product.id, "quantity": 2})
    assert r.status_code == 201
    r = client.post("/orders/", json={"user_id": user_id})
    assert r.status_code == 400


def test_orders_errors_get_and_status_transition(client, db_session):
    user_id = 42

    # Create empty cart then create_order => 400 (panier vide ou inexistant)
    r = client.get(f"/cart/{user_id}")
    assert r.status_code == 200
    r = client.post("/orders/", json={"user_id": user_id})
    assert r.status_code == 400

    # Not found order
    r = client.get("/orders/999999")
    assert r.status_code == 404

    # Coupon not found => 404
    product = Product(name="Produit A", price=100.0, stock=10, active=True)
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    r = client.post(f"/cart/?user_id={user_id}", json={"product_id": product.id, "quantity": 1})
    assert r.status_code == 201
    r = client.post("/orders/", json={"user_id": user_id, "coupon_code": "DOESNTEXIST"})
    assert r.status_code == 404

    # Invalid status transition: pending -> shipped should be rejected => 400
    # (Pour être sûr, on crée une commande directement)
    order = Order(user_id=user_id, total_ht=100.0, total_ttc=120.0, status="pending")
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)

    r = client.patch(f"/orders/{order.id}/status", json={"status": "shipped"})
    assert r.status_code == 400


def test_coupons_routes_success_and_errors(client, db_session, coupon_sample):
    # Duplicate coupon => 409
    payload = {"code": "NEWCUP", "reduction": 10.0, "actif": True}
    r = client.post("/coupons/", json=payload)
    assert r.status_code == 201

    r = client.post("/coupons/", json=payload)
    assert r.status_code == 409

    # Get inactive coupon => 404
    inactive = Coupon(code="OFF", reduction=20.0, actif=False)
    db_session.add(inactive)
    db_session.commit()
    db_session.refresh(inactive)
    r = client.get("/coupons/OFF")
    assert r.status_code == 404

    # Apply valid coupon
    r = client.post("/coupons/apply", json={"coupon_code": coupon_sample.code, "prix": 100.0})
    assert r.status_code == 200
    assert r.json()["coupon_code"] == coupon_sample.code

    # Apply with unknown coupon => 404
    r = client.post("/coupons/apply", json={"coupon_code": "UNKNOWN", "prix": 100.0})
    assert r.status_code == 404

    # Apply with invalid reduction => 400 (forcer ValueError dans appliquer_coupon)
    invalid_coupon = Coupon(code="BAD", reduction=101.0, actif=True)
    db_session.add(invalid_coupon)
    db_session.commit()
    db_session.refresh(invalid_coupon)
    r = client.post("/coupons/apply", json={"coupon_code": invalid_coupon.code, "prix": 100.0})
    assert r.status_code == 400

