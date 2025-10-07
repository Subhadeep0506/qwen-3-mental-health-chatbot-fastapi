import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine(
    os.getenv("DATABASE_URL"),
    connect_args=(
        {"check_same_thread": False}
        if "sqlite" in os.getenv("DATABASE_URL", "")
        else {}
    ),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
