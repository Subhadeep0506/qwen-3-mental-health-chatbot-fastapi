import os
from typing import List

from dotenv import load_dotenv

load_dotenv(".env")


import base64
import datetime
from io import BytesIO

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from core.generate_response import generate_response
from core.safety_score import generate_safety_score
from database.database import Base, SessionLocal, engine
from models.cases import Case
from models.chat_message import ChatHistory
from models.patients import Patient
from utils.file_processor import convert_image_to_base64, convert_pdf_to_images
from utils.message import add_ai_response, get_chat_history
from utils.state import State

state = State()
Base.metadata.create_all(bind=engine)
allowed_file_types = ["image/jpeg", "image/png", "application/pdf"]

app = FastAPI(
    title="Qwen-2.5-VL API",
    description="API for Qwen-2.5-VL model with image and text inputs",
    version="0.0.1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def root():
    return {"message": "Welcome to the Qwen-2.5-VL API"}


@app.post("/predict")
async def predict(
    session_id: str = Query(..., description="Session ID for the conversation"),
    case_id: str = Query(..., description="Case ID for the conversation"),
    patient_id: str = Query(..., description="Patient ID for the conversation"),
    model: str = Query(
        "qwen/qwen3-32b",
        description="Model name or path. Accepted values: `qwen/qwen3-32b`, `deepseek-r1-distill-llama-70b`, `gemma2-9b-it`, `compound-beta`, `llama-3.1-8b-instant`, `llama-3.3-70b-versatile`,`meta-llama/llama-4-maverick-17b-128e-instruct`, `meta-llama/llama-4-scout-17b-16e-instruct`, `meta-llama/llama-guard-4-12b`, `openai/gpt-oss-120b`",
    ),
    model_provider: str = Query(
        "groq", description="Model provider: 'local' or 'groq'"
    ),
    prompt: str = Query(..., description="Prompt for the model"),
    temperature: float = Query(0.7, description="Sampling temperature"),
    top_p: float = Query(1.0, description="Nucleus sampling probability"),
    max_tokens: int = Query(1024, description="Maximum number of tokens to generate"),
    debug: bool = Query(os.getenv("DEBUG") == "1", description="Enable debug mode"),
    files: List[UploadFile] = File(None, description="Image files"),
    db=Depends(get_db),  # Dependency injection for database session
):
    try:
        image_base64s = []
        if files:
            if not all(file.content_type in allowed_file_types for file in files):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file type. Allowed types are: JPEG, PNG, PDF.",
                )
            if files[0].content_type.startswith("image/"):
                for image in files:
                    img = await convert_image_to_base64(image)
                    image_base64s.append(img)
            elif files[0].content_type.startswith("application/pdf"):
                for pdf in files:
                    imgs = await convert_pdf_to_images(pdf)
                    image_base64s.extend(imgs)

        history = get_chat_history(session_id, state.history, db)
        memory = [content for msg in history for content in msg["content"]]
        response, messages = generate_response(
            model=model,
            model_provider=model_provider,
            tokenizer=state.tokenizer,
            images=image_base64s,
            prompt=prompt,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            memory=memory,
            debug=debug,
        )
        safety_score = generate_safety_score(response, debug=not debug)
        state.history = add_ai_response(
            case_id=case_id,
            patient_id=patient_id,
            session_id=session_id,
            content=messages,
            safety=safety_score,
            history=state.history,
            db=db,
        )
        return {"response": response, "safety_score": safety_score}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


### HISTORY ENDPOINTS
@app.get("/history")
async def get_history(
    session_id: str = Query(..., description="Session ID for the conversation"),
    db=Depends(get_db),
):
    try:
        conversations = get_chat_history(session_id, state.history, db=db)
        return {"conversations": conversations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/history/{session_id}")
async def delete_history(
    session_id: str,
    db=Depends(get_db),
):
    try:
        state.history = [h for h in state.history if h["session_id"] != session_id]
        db.query(ChatHistory).filter(ChatHistory.session_id == session_id).delete()
        db.commit()
        return {"detail": "History deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


### PATIENTS ENDPOINTS
@app.get("/patients")
async def get_patients(
    db=Depends(get_db),
):
    try:
        patients = db.query(Patient).all()
        return {"patients": [patient.__dict__ for patient in patients]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/patient/{patient_id}")
async def get_patient(
    patient_id: str,
    db=Depends(get_db),
):
    try:
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        return {"patient": patient.__dict__}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/patient")
async def create_patient(
    patient_id: str = Query(str, description=""),
    name: str = Query(str, description=""),
    age: int = Query(str, description=""),
    gender: str = Query(str, description=""),
    dob: str = Query(str, description=""),
    medical_history: str = Query(str, description=""),
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/patient/{patient_id}")
async def update_patient(
    patient_id: str,
    name: str = Query(None, description="Updated name of the patient"),
    age: int = Query(None, description="Updated age of the patient"),
    gender: str = Query(None, description=""),
    dob: str = Query(None, description=""),
    medical_history: str = Query(None, description=""),
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/patient/{patient_id}")
async def delete_patient(
    patient_id: str,
    db=Depends(get_db),
):
    try:
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        db.delete(patient)
        db.commit()
        return {"detail": "Patient deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


### CASES ENDPOINTS
@app.get("/cases")
async def get_cases(
    db=Depends(get_db),
):
    try:
        cases = db.query(Case).all()
        return {"cases": [case.__dict__ for case in cases]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/case/{case_id}")
async def get_case(
    case_id: str,
    db=Depends(get_db),
):
    try:
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        return {"case": case.__dict__}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/case")
async def create_case(
    case_id: str = Query(..., description="Case ID for the case"),
    patient_id: str = Query(..., description="Patient ID for the case"),
    case_name: str = Query(..., description="Name of the case"),
    description: str = Query(..., description="Description of the case"),
    tags: List[str] = Query([], description="Tags for the case"),
    db=Depends(get_db),
):
    try:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/case/{case_id}")
async def update_case(
    case_id: str,
    case_name: str = Query(None, description="Updated name of the case"),
    description: str = Query(None, description="Updated description of the case"),
    tags: List[str] = Query(None, description="Updated tags for the case"),
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/case/{case_id}")
async def delete_case(
    case_id: str,
    db=Depends(get_db),
):
    try:
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        db.delete(case)
        db.commit()
        return {"detail": "Case deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
