from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import Base, engine, get_db
from models import Patient, Doctor
from schemas import PatientCreate, PatientLogin, DoctorCreate, DoctorLogin, PatientResponse, PatientRecordCreate
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI()

# app = FastAPI()

# Allow your React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:5173"] if using Vite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create all tables
Base.metadata.create_all(bind=engine)

@app.get("/")
def home():
    return {"message": "Medical Portal API is running 🚀"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint to test database connectivity"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        patient_count = db.query(Patient).count()
        return {
            "status": "healthy",
            "database": "connected",
            "patient_count": patient_count
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

# ---------------- PATIENT -----------------
@app.post("/register_patient")
def register_patient(request: PatientCreate, db: Session = Depends(get_db)):
    existing = db.query(Patient).filter(Patient.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_patient = Patient(
        name=request.name,
        email=request.email,
        password=request.password  # in production, hash passwords!
    )
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return {"message": "Patient registered successfully!", "id": new_patient.id}


@app.post("/login_patient")
def login_patient(request: PatientLogin, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.email == request.email).first()
    if not patient or patient.password != request.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful", "patient_id": patient.id}


# Guest endpoint to get all patient records (names and IDs)
@app.get("/get_patients", response_model=List[PatientResponse])
def get_patients(db: Session = Depends(get_db)):
    patients = db.query(Patient).all()
    return patients


# Guest endpoint to get a single patient by ID
@app.get("/get_patient/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


# Endpoint to create/update patient record with problem (consultation details)
@app.post("/patient_record")
async def create_patient_record(request: PatientRecordCreate, db: Session = Depends(get_db)):
    """Create or update patient record with consultation problem details"""
    try:
        print(f"[DEBUG] Received request: patient_id={request.patient_id}, problem='{request.problem[:50] if request.problem else 'None'}...'")
        print(f"[DEBUG] Full request data: {request.dict()}")
        
        # Validate input
        if not request.patient_id:
            raise HTTPException(status_code=400, detail="Patient ID is required")
        
        if not request.problem or not request.problem.strip():
            raise HTTPException(status_code=400, detail="Problem description cannot be empty")
        
        # Find the patient by ID
        patient = db.query(Patient).filter(Patient.id == request.patient_id).first()
        if not patient:
            print(f"[ERROR] Patient not found with ID: {request.patient_id}")
            raise HTTPException(status_code=404, detail=f"Patient not found with ID: {request.patient_id}")
        
        print(f"[DEBUG] Found patient: {patient.name} (ID: {patient.id})")
        
        # Update the problem field (append if existing, or set if new)
        problem_text = request.problem.strip()
        if patient.problem and patient.problem.strip():
            # Append to existing problem with separator
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            patient.problem = f"{patient.problem}\n\n--- Consultation on {timestamp} ---\n{problem_text}"
            print(f"[DEBUG] Appending to existing problem")
        else:
            # Set new problem if none exists
            patient.problem = problem_text
            print(f"[DEBUG] Setting new problem")
        
        # Commit the transaction
        try:
            db.commit()
            db.refresh(patient)
            print(f"[SUCCESS] Successfully saved problem for patient {patient.id}")
            
            # Verify the save worked
            verification = db.query(Patient).filter(Patient.id == request.patient_id).first()
            if verification and verification.problem:
                print(f"[VERIFY] Problem field confirmed in database: {len(verification.problem)} characters")
            else:
                print(f"[WARNING] Problem field may not have been saved correctly")
            
        except Exception as db_error:
            print(f"[ERROR] Database commit failed: {str(db_error)}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to save to database: {str(db_error)}")
        
        return {
            "message": "Patient record updated successfully!",
            "patient_id": patient.id,
            "patient_name": patient.name,
            "problem_saved": True,
            "problem": patient.problem
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Error in create_patient_record: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ---------------- DOCTOR -----------------
@app.post("/register_doctor")
def register_doctor(request: DoctorCreate, db: Session = Depends(get_db)):
    existing = db.query(Doctor).filter(Doctor.email.ilike(request.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_doctor = Doctor(
        email=request.email,
        password=request.password  # in production, hash passwords!
    )
    db.add(new_doctor)
    db.commit()
    db.refresh(new_doctor)
    return {"message": "Doctor registered successfully!", "id": new_doctor.id}


@app.post("/login_doctor")
def login_doctor(request: DoctorLogin, db: Session = Depends(get_db)):
    # Case-insensitive email comparison
    doctor = db.query(Doctor).filter(Doctor.email.ilike(request.email)).first()
    if not doctor:
        raise HTTPException(status_code=401, detail="Doctor not found with this email")
    if doctor.password != request.password:
        raise HTTPException(status_code=401, detail="Invalid password")
    return {"message": "Doctor login successful", "doctor_id": doctor.id}
