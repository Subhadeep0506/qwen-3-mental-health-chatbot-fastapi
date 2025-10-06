import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session
from utils.state import State
from datetime import datetime, timedelta
from models.session_message import SessionMessages
from models.session import ChatSession


def create_session(
    session_id: str, title: str, case_id: str, patient_id: str, db: Session
) -> str:
    """
    Create a new chat session.

    Returns:
        str: Unique identifier for the chat session.
    """
    try:
        session = (
            db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        )
        if not session:
            session = ChatSession(
                session_id=session_id,
                title=title,
                case_id=case_id,
                patient_id=patient_id,
                time_created=datetime.utcnow(),
                time_updated=datetime.utcnow(),
            )
            db.add(session)
            db.commit()
            db.refresh(session)
        return session.session_id
    except Exception as e:
        State.logger.error(f"An error occured while creating session: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occured while creating session: {str(e)}",
        )


def edit_session(session_id: str, title: str, db: Session) -> str:
    """
    Edit an existing chat session.

    Returns:
        str: Unique identifier for the chat session.
    """
    try:
        session = (
            db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        )
        if session:
            session.title = title
            session.time_updated = datetime.utcnow()
            db.commit()
            db.refresh(session)
        return session.session_id if session else None
    except Exception as e:
        State.logger.error(f"An error occured while editing session: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occured while editing session: {str(e)}",
        )


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
            session = (
                db.query(ChatSession)
                .filter(ChatSession.session_id == session_id)
                .first()
            )
            if not session:
                new_session = ChatSession(
                    session_id=session_id,
                    title="New Session",
                    case_id=case_id,
                    patient_id=patient_id,
                    time_created=datetime.utcnow(),
                    time_updated=datetime.utcnow(),
                )
                db.add(new_session)
                db.commit()
                db.refresh(new_session)
            new_message = SessionMessages(
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
        State.logger.error(f"An error occured while adding AI response: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occured while adding AI response: {str(e)}",
        )


def get_chat_history(session_id: str, db: Session):
    """
    Retrieve the chat history for a given session.

    Args:
        session_id (str): Unique identifier for the chat session.

    Returns:
        List[SessionMessages]: List of chat messages for the session.
    """
    try:
        if db:
            history = (
                db.query(SessionMessages)
                .filter(SessionMessages.session_id == session_id)
                .all()
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
        State.logger.error(f"An error occured while getting chat history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occured while getting chat history: {str(e)}",
        )
