from sqlalchemy import Numeric, Column, Integer, String
from sqlalchemy.orm import relationship

from database.database import Base


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

    # One-to-many: Patient -> Case
    cases = relationship(
        "Case",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    # One-to-many: Patient -> SessionMessages (direct messages that reference patient)
    session_messages = relationship(
        "SessionMessages",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
