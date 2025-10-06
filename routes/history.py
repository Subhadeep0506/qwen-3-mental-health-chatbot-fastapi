from fastapi import APIRouter, Depends, HTTPException, Query

from database.database import get_db
from models.chat_message import ChatHistory
from utils.message import get_chat_history
from utils.state import State
from core.auth import token_required, JWTBearer
from utils.state import State

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
        db.query(ChatHistory).filter(ChatHistory.session_id == session_id).delete()
        db.commit()
        return {"detail": "History deleted successfully"}
    except Exception as e:
        State.logger.error(f"An error occured while deleting history: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"An error occured while deleting history: {str(e)}"
        )
