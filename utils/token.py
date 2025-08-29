import os

from fastapi import HTTPException, status
from jose import jwt
from jwt import InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from utils.state import State
from models.token import Token

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_hashed_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, hashed_pass: str) -> bool:
    return password_context.verify(password, hashed_pass)


def verify_token(token: str, db: Session):
    token_record = db.query(Token).filter(Token.access_token == token).first()
    if not token_record or not token_record.status:
        State.logger.error("Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
    return token_record


def decodeJWT(jwtoken: str):
    try:
        payload = jwt.decode(
            jwtoken, os.getenv("JWT_SECRET_KEY"), os.getenv("JWT_ALGORITHM")
        )
        return payload
    except InvalidTokenError:
        return None
