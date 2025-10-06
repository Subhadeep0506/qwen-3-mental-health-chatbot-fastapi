from sqlalchemy import JSON, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from database.database import Base, engine
from models.cases import Case
from models.patients import Patient


class ChatSession(Base):
    __tablename__ = "chat_session"

    session_id = Column(String, primary_key=True, nullable=False, index=True)
    title = Column(String)
    case_id = Column(
        String,
        ForeignKey(Case.case_id),
        nullable=False,
    )
    patient_id = Column(
        String,
        ForeignKey(Patient.patient_id),
        nullable=False,
    )
    time_created = Column(String)
    time_updated = Column(String)

    # Relationship with cascade delete
    messages = relationship(
        "SessionMessages", back_populates="session", cascade="all, delete-orphan"
    )
