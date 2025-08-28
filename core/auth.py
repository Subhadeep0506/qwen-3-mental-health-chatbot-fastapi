import os
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Union

import jwt
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from sqlalchemy import desc

from models.token import Token
from utils.token import decodeJWT


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearer, self
        ).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=403, detail="Invalid authentication scheme."
                )
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(
                    status_code=403, detail="Invalid token or expired token."
                )
            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")

    def verify_jwt(self, jwtoken: str) -> bool:
        isTokenValid: bool = False
        try:
            payload = decodeJWT(jwtoken)
        except Exception:
            payload = None
        if payload:
            isTokenValid = True
        return isTokenValid


def create_access_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(
            minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES"))
        )
    if "_sa_instance_state" in subject:
        del subject["_sa_instance_state"]
    to_encode = {"exp": expires_delta, "sub": subject}
    encoded_jwt = jwt.encode(
        to_encode, os.getenv("JWT_SECRET_KEY"), os.getenv("JWT_ALGORITHM")
    )
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(
            minutes=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_MINUTES"))
        )
    to_encode = {"exp": expires_delta, "sub": subject}
    encoded_jwt = jwt.encode(
        to_encode, os.getenv("JWT_SECRET_KEY"), os.getenv("JWT_ALGORITHM")
    )
    return encoded_jwt


def token_required(func):
    """Verifies the JWT token. Checks if user is loggedin."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        payload = decodeJWT(kwargs["dependencies"])
        user_id = payload["sub"]["user_id"]
        data = (
            kwargs["db"]
            .query(Token)
            .filter_by(
                user_id=user_id, access_token=kwargs["dependencies"], status=True
            )
            .order_by(desc(Token.time_created))
            .first()
        )
        if data:
            return func(*args, **kwargs)

        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token."
            )

    return wrapper
