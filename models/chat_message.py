from sqlalchemy import JSON, Column, ForeignKey, String

from database.database import Base, engine
from models.cases import Case
from models.patients import Patient


class ChatHistory(Base):
    __tablename__ = "chat_history"

    message_id = Column(String, primary_key=True, nullable=False, index=True)
    session_id = Column(String, nullable=False)
    case_id = Column(String, ForeignKey(Case.case_id), nullable=False,)
    patient_id = Column(
        String, ForeignKey(Patient.patient_id), nullable=False,
    )
    content = Column(JSON, nullable=False)
    safety = Column(JSON, nullable=False)
