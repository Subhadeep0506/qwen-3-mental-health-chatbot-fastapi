from sqlalchemy import JSON, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from database.database import Base
from models.cases import Case
from models.patients import Patient


class ChatSession(Base):
    __tablename__ = "chat_session"

    session_id = Column(String, primary_key=True, nullable=False, index=True)
    title = Column(String)
    case_id = Column(
        String,
        ForeignKey("cases.case_id", ondelete="CASCADE"),
        nullable=False,
    )
    patient_id = Column(
        String,
        ForeignKey("patients.patient_id", ondelete="CASCADE"),
        nullable=False,
    )
    time_created = Column(String)
    time_updated = Column(String)

    # Relationship with cascade delete (ORM-level)
    messages = relationship(
        "SessionMessages",
        back_populates="chat_session",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # Relationship back to Case and Patient
    case = relationship("Case", back_populates="chat_sessions")
    patient = relationship("Patient")
