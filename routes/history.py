from fastapi import APIRouter, Depends, HTTPException, Query

from database.database import get_db
from models.session_message import SessionMessages
from models.session import ChatSession
from controllers.message import get_chat_history, create_session, edit_session
from utils.state import State
from controllers.auth import token_required, JWTBearer

router = APIRouter()


@router.get("/messages/{session_id}")
@token_required
async def get_session_messages(
    session_id: str,
    dependencies=Depends(JWTBearer()),
    db=Depends(get_db),
):
    try:
        conversations = get_chat_history(session_id, db=db)
        return {"conversations": conversations}
    except Exception as e:
        State.logger.error(f"An error occured while fetching history: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"An error occured while fetching history: {str(e)}"
        )


@router.post("/sessions")
@token_required
async def create_session_(
    session_id: str = Query(None, description="Unique identifier for the session."),
    case_id: str = Query(..., description="Unique identifier for the case."),
    patient_id: str = Query(..., description="Unique identifier for the patient."),
    title: str = Query(..., description="Title of the chat session."),
    dependencies=Depends(JWTBearer()),
    db=Depends(get_db),
):
    try:
        session_id = create_session(
            session_id=session_id,
            case_id=case_id,
            patient_id=patient_id,
            title=title,
            db=db,
        )
        return {
            "detail": f"Session {session_id} created successfully",
        }
    except Exception as e:
        State.logger.error(f"An error occured while creating session: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"An error occured while creating session: {str(e)}"
        )


@router.put("/sessions/{session_id}")
@token_required
async def edit_session_title(
    session_id: str,
    title: str = Query(..., description="New title of the chat session."),
    dependencies=Depends(JWTBearer()),
    db=Depends(get_db),
):
    try:
        updated_session_id = edit_session(session_id=session_id, title=title, db=db)
        return {
            "detail": f"Session {updated_session_id} updated successfully",
        }
    except Exception as e:
        State.logger.error(f"An error occured while editing session: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"An error occured while editing session: {str(e)}"
        )


@router.get("/sessions")
@token_required
async def get_sessions(
    session_id: str,
    dependencies=Depends(JWTBearer()),
    db=Depends(get_db),
):
    try:
        conversations = get_chat_history(session_id, db=db)
        return {"conversations": conversations}
    except Exception as e:
        State.logger.error(f"An error occured while fetching history: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"An error occured while fetching history: {str(e)}"
        )


@router.delete("/session/{session_id}")
@token_required
async def delete_session(
    session_id: str,
    dependencies=Depends(JWTBearer()),
    db=Depends(get_db),
):
    try:
        # Check if session exists
        session = (
            db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        )

        if not session:
            raise HTTPException(
                status_code=404, detail=f"Session {session_id} not found"
            )

        # Delete the ChatSession - this will cascade delete all related SessionMessages
        db.delete(session)
        db.commit()

        return {
            "detail": f"Session {session_id} and all its messages deleted successfully"
        }
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        State.logger.error(f"An error occured while deleting session: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"An error occured while deleting session: {str(e)}"
        )
