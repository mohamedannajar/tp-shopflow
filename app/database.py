import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./shopflow.db")


def create_db_engine(url=DATABASE_URL):
    if url == "sqlite:///:memory:":
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
    elif url.startswith("sqlite"):
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False}
        )

        @event.listens_for(engine, "connect")
        def set_fk(conn, _):
            conn.cursor().execute("PRAGMA foreign_keys=ON")

        return engine

    return create_engine(url)


engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()