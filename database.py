"""
SQLAlchemy database setup for the Extraction Job API.
Supports SQLite (local dev) and PostgreSQL (Lambda/RDS).
"""

import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_models import Base

# DATABASE_URL for PostgreSQL (Lambda/RDS); DB_PATH for SQLite (local dev)
DATABASE_URL = os.environ.get("DATABASE_URL")
DB_PATH = os.environ.get("DB_PATH", "extraction_jobs.db")

# Default URL: SQLite for local dev when DATABASE_URL is not set
def _get_default_url() -> str:
    if DATABASE_URL:
        return DATABASE_URL
    return f"sqlite:///{DB_PATH}"

_engines: dict[str, object] = {}
_session_factories: dict[str, object] = {}


def get_engine(db_url: str | None = None):
    """Return SQLAlchemy engine for the given URL (cached per URL)."""
    url = db_url or _get_default_url()
    if url not in _engines:
        if url.startswith("sqlite"):
            _engines[url] = create_engine(
                url,
                connect_args={"check_same_thread": False},
            )
        else:
            # PostgreSQL: Lambda-friendly pooling
            _engines[url] = create_engine(
                url,
                pool_pre_ping=True,
                pool_size=2,
                max_overflow=0,
            )
    return _engines[url]


def get_session_factory(db_url: str | None = None):
    """Return session factory for the given URL (cached per URL)."""
    url = db_url or _get_default_url()
    if url not in _session_factories:
        engine = get_engine(url)
        _session_factories[url] = sessionmaker(
            autocommit=False, autoflush=False, bind=engine
        )
    return _session_factories[url]


def init_db(db_url: str | None = None) -> None:
    """Create all tables if they do not exist."""
    url = db_url or _get_default_url()
    engine = get_engine(url)
    Base.metadata.create_all(engine)


@contextmanager
def get_session(db_url: str | None = None):
    """Context manager yielding a database session."""
    url = db_url or _get_default_url()
    SessionLocal = get_session_factory(url)
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
