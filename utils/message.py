import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.chat_message import ChatHistory


def add_ai_response(
    case_id: str,
    patient_id: str,
    session_id: str,
    content: dict,
    safety: dict,
    history: list = [],
    db: Session = None,
):
    """
    Add an AI response to the chat history.

    Args:
        session_id (str): Unique identifier for the chat session.
        content (dict): Content of the AI response.
        safety (dict): Safety evaluation of the AI response.
    """
    try:
        if db:
            new_message = ChatHistory(
                message_id=str(uuid.uuid4()),
                session_id=session_id,
                case_id=case_id,
                patient_id=patient_id,
                content=content,
                safety=safety,
            )
            db.add(new_message)
            db.commit()
            db.refresh(new_message)
        history.append(
            {
                "session_id": session_id,
                "content": content,
                "safety": safety,
            }
        )
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_chat_history(session_id: str, db: Session):
    """
    Retrieve the chat history for a given session.

    Args:
        session_id (str): Unique identifier for the chat session.

    Returns:
        List[ChatHistory]: List of chat messages for the session.
    """
    try:
        if db:
            history = (
                db.query(ChatHistory).filter(ChatHistory.session_id == session_id).all()
            )
            history = [
                {
                    "session_id": msg.session_id,
                    "content": msg.content,
                    "safety": msg.safety,
                }
                for msg in history
            ]
            return history
        session_history = [msg for msg in history if msg["session_id"] == session_id]
        return session_history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
