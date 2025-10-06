from sqlalchemy import JSON, Column, ForeignKey, String, Boolean

from database.database import Base, engine
from models.cases import Case
from models.session import Session
from models.patients import Patient


class SessionMessages(Base):
    __tablename__ = "session_messages"

    message_id = Column(String, primary_key=True, nullable=False, index=True)
    session_id = Column(String, ForeignKey(Session.session_id), nullable=False)
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
    content = Column(JSON, nullable=False)
    safety = Column(JSON, nullable=False)
    feedback = Column(String)
    like = Column(Boolean)
