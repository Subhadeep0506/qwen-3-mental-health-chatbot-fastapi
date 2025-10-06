from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from database.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, nullable=False, primary_key=True, index=True)
    name = Column(String, nullable=True)
    email = Column(String, nullable=False)
    password = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    role = Column(String, nullable=False)
    time_created = Column(String, nullable=True)
    time_updated = Column(String, nullable=True)

    # Relationship to tokens (one-to-many)
    tokens = relationship("Token", back_populates="user", cascade="all, delete-orphan")
