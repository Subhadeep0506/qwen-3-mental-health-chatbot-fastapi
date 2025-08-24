from sqlalchemy import JSON, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from database.database import Base, engine
from models.patients import Patient


class Case(Base):
    __tablename__ = "cases"

    case_id = Column(String, primary_key=True, nullable=False, index=True)
    patient_id = Column(
        String,
        ForeignKey(Patient.patient_id),
        nullable=False,
    )
    case_name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    time_created = Column(String, nullable=False)
    time_updated = Column(String, nullable=False)
    tags = Column(JSON, nullable=True)

    chat_histories = relationship("ChatHistory", backref="cases", cascade="all, delete")
