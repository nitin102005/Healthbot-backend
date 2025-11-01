from sqlalchemy import Column, Integer, String, Text
from database import Base

class Patient(Base):
    __tablename__ = "patient_records"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    problem = Column(Text, default="")  # Store consultation problem/details

class Doctor(Base):
    __tablename__ = "doctor_records"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
