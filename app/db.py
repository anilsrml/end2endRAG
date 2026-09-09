from collections.abc import Generator
from functools import lru_cache

from pgvector.psycopg import register_vector
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


@lru_cache
def get_engine() -> Engine:
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)

    @event.listens_for(engine, "connect")
    def _register_vector(dbapi_connection, _connection_record) -> None:
        register_vector(dbapi_connection)

    return engine


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()

