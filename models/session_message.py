from sqlalchemy import JSON, Column, ForeignKey, String, Boolean, Integer
from sqlalchemy.orm import relationship
import datetime
from database.database import Base, engine
from models.cases import Case
from models.patients import Patient
from models.session import ChatSession


class SessionMessages(Base):
    __tablename__ = "session_messages"

    message_id = Column(String, primary_key=True, nullable=False, index=True)
    session_id = Column(String, ForeignKey(ChatSession.session_id), nullable=False)
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
    feedback = Column(String, default=None)
    like = Column(String, default=None)
    stars = Column(Integer, default=0)
    content = Column(JSON, nullable=False)
    safety = Column(JSON, nullable=False)
    timestamp = Column(String, nullable=False, default=f"{datetime.datetime.utcnow()}")

    # Back reference to ChatSession
    session = relationship("ChatSession", back_populates="session_messages", cascade="all, delete")
