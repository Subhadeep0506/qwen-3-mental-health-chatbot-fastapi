import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from core.auth import JWTBearer, decodeJWT, token_required
from database.database import get_db
from models.cases import Case
from models.patients import Patient
from utils.state import State
router = APIRouter()


@router.get("/")
@token_required
async def get_cases(
    dependencies=Depends(JWTBearer()),
    db=Depends(get_db),
):
    try:
        cases = db.query(Case).all()
        return {"cases": [case.__dict__ for case in cases]}
    except Exception as e:
        State.logger.error(f"An error occured while fetching all cases: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occured while fetching all cases: {str(e)}")


@router.get("/{case_id}")
@token_required
async def get_case(
    case_id: str,
    dependencies=Depends(JWTBearer()),
    db=Depends(get_db),
):
    try:
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            State.logger.error(f"Case with ID {case_id} not found")
            raise HTTPException(status_code=404, detail="Case not found")
        return {"case": case.__dict__}
    except HTTPException:
        raise
    except Exception as e:
        State.logger.error(f"An error occured while fetching case: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occured while fetching case: {str(e)}")


@router.post("/")
@token_required
async def create_case(
    case_id: str = Query(..., description="Case ID for the case"),
    patient_id: str = Query(..., description="Patient ID for the case"),
    case_name: str = Query(..., description="Name of the case"),
    description: str = Query(..., description="Description of the case"),
    tags: List[str] = Query([], description="Tags for the case"),
    dependencies=Depends(JWTBearer()),
    db=Depends(get_db),
):
    try:
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not patient:
            State.logger.error(f"Patient with ID {patient_id} not found")
            raise HTTPException(status_code=404, detail="Patient not found")
        existing_case = db.query(Case).filter(Case.case_id == case_id).first()
        if existing_case:
            State.logger.error(f"Case with ID {case_id} already exists")
            raise HTTPException(status_code=400, detail="Case ID already exists")
        new_case = Case(
            case_id=case_id,
            patient_id=patient_id,
            case_name=case_name,
            description=description,
            time_created=datetime.datetime.now(datetime.UTC).isoformat(),
            time_updated=datetime.datetime.now(datetime.UTC).isoformat(),
            tags=tags,
        )
        db.add(new_case)
        db.commit()
        db.refresh(new_case)
        return {"case": new_case.__dict__}
    except HTTPException:
        raise
    except Exception as e:
        State.logger.error(f"An error occured while creating new case: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occured while creating new case: {str(e)}")


@router.put("/{case_id}")
@token_required
async def update_case(
    case_id: str,
    case_name: str = Query(None, description="Updated name of the case"),
    description: str = Query(None, description="Updated description of the case"),
    tags: List[str] = Query(None, description="Updated tags for the case"),
    dependencies=Depends(JWTBearer()),
    db=Depends(get_db),
):
    try:
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        if case_name:
            case.case_name = case_name
        if description:
            case.description = description
        if tags is not None:
            case.tags = tags
        case.time_updated = datetime.datetime.now(datetime.UTC).isoformat()
        db.commit()
        db.refresh(case)
        return {"case": case.__dict__}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{case_id}")
@token_required
async def delete_case(
    case_id: str,
    dependencies=Depends(JWTBearer()),
    db=Depends(get_db),
):
    try:
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        db.delete(case)
        db.commit()
        return {"detail": "Case deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
