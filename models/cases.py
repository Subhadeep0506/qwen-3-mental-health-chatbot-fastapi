from sqlalchemy import JSON, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from database.database import Base
from models.patients import Patient
from models.user import User


class Case(Base):
    __tablename__ = "cases"

    case_id = Column(String, primary_key=True, nullable=False, index=True)
    patient_id = Column(
        String,
        ForeignKey("patients.patient_id", ondelete="CASCADE"),
        nullable=False,
    )
    case_name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    time_created = Column(String, nullable=True)
    time_updated = Column(String, nullable=True)
    tags = Column(JSON, nullable=True)
    priority = Column(String, nullable=True)

    # Relationship to parent patient
    patient = relationship("Patient", back_populates="cases")

    # One-to-many: Case -> ChatSession (sessions under this case)
    chat_sessions = relationship(
        "ChatSession",
        back_populates="case",
        cascade="all, delete-orphan",
    )

    # Also keep messages that reference this case directly
    session_messages = relationship(
        "SessionMessages",
        back_populates="case",
        cascade="all, delete-orphan",
    )
