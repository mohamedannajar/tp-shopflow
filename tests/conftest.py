import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Product, Cart, CartItem, Order, OrderItem, Coupon


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