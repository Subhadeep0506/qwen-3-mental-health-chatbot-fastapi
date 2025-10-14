import os
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from controllers.generate_response import generate_response
from controllers.safety_score import generate_safety_score
from database.database import get_db
from utils.file_processor import convert_image_to_base64, convert_pdf_to_images
from controllers.message import (
    add_ai_response,
    edit_feedback,
    get_chat_history,
    like_ai_message,
    submit_feedback,
)
from models.cases import Case
from models.patients import Patient
from utils.state import State
from controllers.auth import token_required, JWTBearer
from utils.state import State

router = APIRouter()


@router.post("/")
@token_required
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
    dependencies=Depends(JWTBearer()),
    db=Depends(get_db),  # Dependency injection for database session
):
    try:
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            State.logger.error(f"Case with ID {case_id} not found")
            raise HTTPException(status_code=404, detail="Case not found")
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not patient:
            State.logger.error(f"Patient with ID {patient_id} not found")
            raise HTTPException(status_code=404, detail="Patient not found")
        image_base64s = []
        if files:
            if not all(
                file.content_type in ["image/jpeg", "image/png", "application/pdf"]
                for file in files
            ):
                State.logger.error("Invalid file type")
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

        history = get_chat_history(session_id, db)
        memory = [content for msg in history for content in msg["content"]]
        response, messages = generate_response(
            model=model,
            model_provider=model_provider,
            tokenizer=State.tokenizer,
            images=image_base64s,
            prompt=prompt,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            memory=memory,
            debug=debug,
        )
        safety_score = generate_safety_score(response, debug=debug)
        history = add_ai_response(
            case_id=case_id,
            patient_id=patient_id,
            session_id=session_id,
            content=messages,
            safety=safety_score,
            history=history,
            db=db,
        )
        return {"response": response, "safety_score": safety_score}
    except HTTPException:
        raise
    except Exception as e:
        State.logger.error(f"An error occured while generating response: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occured while generating response: {str(e)}",
        )


@router.post("/like-message/{message_id}")
@token_required
async def like_ai_message_(
    message_id: int,
    like: bool = Query(..., description="Like (true) or dislike (false) the message"),
    dependencies=Depends(JWTBearer()),
    db=Depends(get_db),
):
    try:
        res = like_ai_message(message_id=message_id, like=like, db=db)
        if res:
            return res
        return {"detail": "Message not found"}
    except HTTPException:
        raise
    except Exception as e:
        State.logger.error(f"An error occured while liking message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occured while liking message: {str(e)}",
        )


@router.post("/submit-feedback/{message_id}")
@token_required
async def submit_feedback_(
    message_id: int,
    feedback: str,
    stars: int = Query(None, description="Star rating from 1 to 5"),
    dependencies=Depends(JWTBearer()),
    db=Depends(get_db),
):
    try:
        res = submit_feedback(
            message_id=message_id, feedback=feedback, stars=stars, db=db
        )
        if res:
            return res
        return {"detail": "Message not found"}
    except HTTPException:
        raise
    except Exception as e:
        State.logger.error(f"An error occured while submitting feedback: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occured while submitting feedback: {str(e)}",
        )


@router.put("/edit-feedback/{message_id}")
@token_required
async def edit_feedback_(
    message_id: int,
    feedback: str = Query(None, description="Updated feedback text"),
    stars: int = Query(None, description="Updated star rating from 1 to 5"),
    dependencies=Depends(JWTBearer()),
    db=Depends(get_db),
):
    try:
        res = edit_feedback(
            message_id=message_id, feedback=feedback, stars=stars, db=db
        )
        if res:
            return res
        return {"detail": "Message not found"}
    except HTTPException:
        raise
    except Exception as e:
        State.logger.error(f"An error occured while editing feedback: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occured while editing feedback: {str(e)}",
        )
