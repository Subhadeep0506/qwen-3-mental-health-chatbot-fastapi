from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from database.database import Base, engine
from models.user import User


class Token(Base):
    __tablename__ = "tokens"

    token_id = Column(String, nullable=False, primary_key=True, index=True)
    user_id = Column(String, ForeignKey(User.user_id), nullable=False)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    status = Column(Boolean, nullable=False)
    time_created = Column(String, nullable=True)
    time_updated = Column(String, nullable=True)

    user = relationship("User", backref="tokens", cascade="all, delete")
