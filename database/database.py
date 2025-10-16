import os
import logging

# Ensure SQLite enforces foreign key constraints (so ON DELETE CASCADE works)
from sqlalchemy import event
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import OperationalError, DBAPIError, DisconnectionError

engine = create_engine(
    os.getenv("DATABASE_URL"),
    connect_args=(
        {"check_same_thread": False}
        if "sqlite" in os.getenv("DATABASE_URL", "")
        else {}
    ),
    # Help detect and recycle stale/closed connections (useful for SSL disconnects)
    pool_pre_ping=True,
)


url = os.getenv("DATABASE_URL", "")
if "sqlite" in url:

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        except Exception:
            # best-effort; if it fails, let SQLAlchemy raise on FK operations
            pass


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class DatabaseConnectionError(Exception):
    """Raised when the DB connection fails (e.g. psycopg2 OperationalError).

    Routes can catch this and return 503 / log as needed.
    """


def get_db():
    db = SessionLocal()
    try:
        try:
            yield db
        except (OperationalError, DBAPIError, DisconnectionError) as e:
            # Log the original DBAPI error for diagnostics; re-raise custom error
            logging.getLogger("app.database").exception(
                "Database operational error: %s", e
            )
            raise DatabaseConnectionError(str(e)) from e
    finally:
        db.close()
