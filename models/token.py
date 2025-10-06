from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from database.database import Base, engine
from models.user import User


class Token(Base):
    __tablename__ = "tokens"

    token_id = Column(String, nullable=False, primary_key=True, index=True)
    # Add ondelete cascade so DB can clean rows if foreign key supported; keep manual delete fallback.
    user_id = Column(
        String, ForeignKey(User.user_id, ondelete="CASCADE"), nullable=False
    )
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    status = Column(Boolean, nullable=False)
    time_created = Column(String, nullable=True)
    time_updated = Column(String, nullable=True)

    # Proper relationship direction: tokens belong to a user. Deleting a user should delete tokens (handled manually in route for sqlite fallback).
    user = relationship("User", back_populates="tokens")
