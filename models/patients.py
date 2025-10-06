from sqlalchemy import Numeric, Column, Integer, String
from sqlalchemy.orm import relationship

from database.database import Base, engine


class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(String, nullable=False, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    dob = Column(String, nullable=True)
    height = Column(String, nullable=True)
    weight = Column(String, nullable=True)
    medical_history = Column(String, nullable=True)
    time_created = Column(String, nullable=True)
    time_updated = Column(String, nullable=True)

    cases = relationship("Case", backref="patients", cascade="all, delete")
    chat_histories = relationship(
        "SessionMessages", backref="patients", cascade="all, delete"
    )
