from sqlalchemy import JSON, Column, Integer, String
from sqlalchemy.orm import relationship

from database.database import Base, engine


class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(String, nullable=False, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    dob = Column(String, nullable=False)
    medical_history = Column(String, nullable=True)
    time_created = Column(String, nullable=False)
    time_updated = Column(String, nullable=False)

    cases = relationship("Case", backref="patients", cascade="all, delete")
    chat_histories = relationship(
        "ChatHistory", backref="patients", cascade="all, delete"
    )
