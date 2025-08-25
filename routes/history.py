from fastapi import APIRouter, Depends, HTTPException, Query

from database.database import get_db
from models.chat_message import ChatHistory
from utils.message import get_chat_history
from utils.state import State

router = APIRouter()


@router.get("/{session_id}")
async def get_history(
    session_id: str,
    db=Depends(get_db),
):
    try:
        conversations = get_chat_history(session_id, db=db)
        return {"conversations": conversations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}")
async def delete_history(
    session_id: str,
    db=Depends(get_db),
):
    try:
        db.query(ChatHistory).filter(ChatHistory.session_id == session_id).delete()
        db.commit()
        return {"detail": "History deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
