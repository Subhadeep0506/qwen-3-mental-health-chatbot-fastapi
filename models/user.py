from sqlalchemy import JSON, Column, Integer, String
from sqlalchemy.orm import relationship

from database.database import Base, engine


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, nullable=False, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    role = Column(String, nullable=False)
    time_created = Column(String, nullable=False)
    time_updated = Column(String, nullable=False)
