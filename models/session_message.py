from sqlalchemy import JSON, Column, ForeignKey, String, Boolean, Integer
from sqlalchemy.orm import relationship
import datetime
from database.database import Base
from models.cases import Case
from models.patients import Patient
from models.session import ChatSession


class SessionMessages(Base):
    __tablename__ = "session_messages"

    message_id = Column(String, primary_key=True, nullable=False, index=True)
    session_id = Column(
        String,
        ForeignKey("chat_session.session_id", ondelete="CASCADE"),
        nullable=False,
    )
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
    feedback = Column(String, default=None)
    like = Column(String, default=None)
    stars = Column(Integer, default=0)
    content = Column(JSON, nullable=False)
    safety = Column(JSON, nullable=False)
    timestamp = Column(String, nullable=False, default=f"{datetime.datetime.utcnow()}")

    # Relationships back to parents
    session = relationship("ChatSession", back_populates="messages")
    case = relationship("Case", back_populates="session_messages")
    patient = relationship("Patient", back_populates="session_messages")
