import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from faker import Faker

from app.database import Base, get_db
from app.main import app
from app.models import Product, Cart, CartItem, Order, OrderItem, Coupon

fake = Faker("fr_FR")


# =========================
# Fixtures TP1 - unit tests
# =========================

@pytest.fixture(scope="function")
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def product_sample(db_session):
    p = Product(
        name="Laptop Pro",
        price=999.99,
        stock=10,
        category="informatique",
        description="Ordinateur portable",
        active=True,
    )
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


@pytest.fixture
def coupon_sample(db_session):
    c = Coupon(
        code="PROMO20",
        reduction=20.0,
        actif=True,
    )
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


# ==============================
# Fixtures TP2 - integration API
# ==============================

@pytest.fixture(scope="module")
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def api_product(client):
    response = client.post(
        "/products/",
        json={
            "name": "Clavier Mécanique",
            "price": 89.99,
            "stock": 25,
            "category": "peripheriques",
        },
    )
    assert response.status_code == 201
    data = response.json()
    yield data
    client.delete(f"/products/{data['id']}")


@pytest.fixture
def api_coupon(client):
    response = client.post(
        "/coupons/",
        json={
            "code": "TEST10",
            "reduction": 10.0,
            "actif": True,
        },
    )
    assert response.status_code == 201
    yield response.json()


# ======================
# Fixtures Faker - TP2
# ======================

@pytest.fixture
def fake_product_data():
    return {
        "name": fake.catch_phrase()[:50],
        "price": round(
            fake.pyfloat(min_value=1, max_value=2000, right_digits=2),
            2
        ),
        "stock": fake.random_int(min=0, max=500),
        "category": fake.random_element(
            ["informatique", "peripheriques", "audio", "gaming"]
        ),
        "description": fake.sentence(nb_words=10),
    }


@pytest.fixture
def multiple_products(client):
    faker_inst = Faker()
    products = []

    for i in range(5):
        response = client.post(
            "/products/",
            json={
                "name": faker_inst.word().capitalize() + f" {i}",
                "price": round(10.0 + i * 20, 2),
                "stock": 10,
            },
        )
        assert response.status_code == 201
        products.append(response.json())

    yield products

    for p in products:
        client.delete(f"/products/{p['id']}")