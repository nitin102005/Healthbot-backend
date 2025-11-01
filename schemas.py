from pydantic import BaseModel, EmailStr
from typing import Optional

class PatientCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class PatientLogin(BaseModel):
    email: EmailStr
    password: str

class DoctorCreate(BaseModel):
    email: EmailStr
    password: str

class DoctorLogin(BaseModel):
    email: EmailStr
    password: str

class PatientResponse(BaseModel):
    id: int
    name: str
    email: str
    problem: Optional[str] = None

    class Config:
        from_attributes = True

class PatientRecordCreate(BaseModel):
    patient_id: int
    problem: str
