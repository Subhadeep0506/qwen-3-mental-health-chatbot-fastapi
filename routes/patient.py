import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from core.auth import JWTBearer, token_required
from database.database import get_db
from models.patients import Patient

router = APIRouter()


@router.get("/")
@token_required
async def get_patients(
    dependencies=Depends(JWTBearer()),
    db=Depends(get_db),
):
    try:
        patients = db.query(Patient).all()
        return {"patients": [patient.__dict__ for patient in patients]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{patient_id}")
@token_required
async def get_patient(
    patient_id: str,
    dependencies=Depends(JWTBearer()),
    db=Depends(get_db),
):
    try:
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        return {"patient": patient.__dict__}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
@token_required
async def create_patient(
    patient_id: str = Query(str, description=""),
    name: str = Query(str, description=""),
    age: int = Query(str, description=""),
    gender: str = Query(str, description=""),
    dob: str = Query(str, description=""),
    medical_history: str = Query(str, description=""),
    dependencies=Depends(JWTBearer()),
    db=Depends(get_db),
):
    try:
        new_patient = Patient(
            patient_id=patient_id,
            name=name,
            age=age,
            gender=gender,
            dob=dob,
            medical_history=medical_history,
            time_created=datetime.datetime.now(datetime.UTC).isoformat(),
            time_updated=datetime.datetime.now(datetime.UTC).isoformat(),
        )
        db.add(new_patient)
        db.commit()
        db.refresh(new_patient)
        return {"patient": new_patient.__dict__}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{patient_id}")
@token_required
async def update_patient(
    patient_id: str,
    name: str = Query(None, description="Updated name of the patient"),
    age: int = Query(None, description="Updated age of the patient"),
    gender: str = Query(None, description=""),
    dob: str = Query(None, description=""),
    medical_history: str = Query(None, description=""),
    dependencies=Depends(JWTBearer()),
    db=Depends(get_db),
):
    try:
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        if name:
            patient.name = name
        if age:
            patient.age = age
        if gender:
            patient.gender = gender
        if dob:
            patient.dob = dob
        if medical_history:
            patient.medical_history = medical_history
        patient.time_updated = datetime.datetime.now(datetime.UTC).isoformat()
        db.commit()
        db.refresh(patient)
        return {"patient": patient.__dict__}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{patient_id}")
@token_required
async def delete_patient(
    patient_id: str,
    dependencies=Depends(JWTBearer()),
    db=Depends(get_db),
):
    try:
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        db.delete(patient)
        db.commit()
        return {"detail": "Patient deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
