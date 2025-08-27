from sqlalchemy import JSON, Column, Integer, String
from sqlalchemy.orm import relationship

from database.database import Base, engine


class Token(Base):
    __tablename__ = "tokens"

    user_id = Column(String, nullable=False, primary_key=True, index=True)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    status = Column(String, nullable=False)
    time_created = Column(String, nullable=True)
    time_updated = Column(String, nullable=True)
