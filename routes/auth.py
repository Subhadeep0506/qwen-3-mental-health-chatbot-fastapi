import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, or_
from uuid import uuid4
from core.auth import (
    JWTBearer,
    create_access_token,
    create_refresh_token,
    decodeJWT,
    token_required,
)
from database.database import get_db
from models.token import Token
from models.user import User
from utils.token import get_hashed_password, verify_password
from utils.state import State
router = APIRouter()


@router.post("/register")
async def register_user(
    user_id: str = Query(str, description=""),
    name: str = Query(None, description=""),
    email: str = Query(str, description=""),
    password: str = Query(str, description=""),
    phone: str = Query(None, description=""),
    role: str = Query("user", description=""),
    db=Depends(get_db),
):
    try:
        user = db.query(User).filter(or_(User.user_id==user_id, User.email==email)).first()
        if user:
            State.logger.error("User with email already exists")
            raise HTTPException(status_code=400, detail="User with email already exists")
        new_user = User(
            user_id=user_id,
            name=name,
            email=email,
            password=get_hashed_password(password),
            phone=phone,
            role=role,
            time_created=datetime.datetime.now(datetime.UTC).isoformat(),
            time_updated=datetime.datetime.now(datetime.UTC).isoformat(),
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"message": "User created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        State.logger.error(f"An error occured while registering user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occured while registering user: {str(e)}")


@router.post("/login")
async def login_user(
    email: str = Query(str, description=""),
    password: str = Query(str, description=""),
    db=Depends(get_db),
):
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password):
            State.logger.error("Invalid credentials")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        access_token = create_access_token(subject=user.__dict__)
        refresh_token = create_refresh_token(subject=user.user_id)
        # Logout of previous session
        token = (
            db.query(Token)
            .filter_by(user_id=user.user_id, status=True)
            .order_by(desc(Token.time_created))
            .first()
        )
        if token:
            token.status = False
            token.time_updated = datetime.datetime.now(datetime.UTC).isoformat()
            db.add(token)
            db.commit()
            db.refresh(token)

        new_token = Token(
            token_id=str(uuid4()),
            user_id=user.user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            status=True,
            time_created=datetime.datetime.now(datetime.UTC).isoformat(),
            time_updated=datetime.datetime.now(datetime.UTC).isoformat(),
        )
        db.add(new_token)
        db.commit()
        db.refresh(new_token)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    except HTTPException:
        raise
    except Exception as e:
        State.logger.error(f"An error occured while login: {str(e)}")
        raise HTTPException(status_code=500,  detail=f"An error occured while login: {str(e)}")


@router.post("/refresh")
@token_required
async def refresh_token(
    refresh_token: str = Query(str, description=""),
    dependencies=Depends(JWTBearer()),
    db=Depends(get_db),
):
    try:
        payload = decodeJWT(refresh_token)
        if not payload:
            State.logger.error("Invalid refresh token")
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        user_id = payload["sub"]
        user = await db.query(User).filter(User.user_id == user_id).first()
        if not user:
            State.logger.error("User not found")
            raise HTTPException(status_code=404, detail="User not found")
        new_access_token = create_access_token(subject=user.__dict__)
        new_refresh_token = create_refresh_token(subject=user.user_id)
        token = (
            db.query(Token)
            .filter_by(user_id=user_id, access_token=dependencies, status=True)
            .order_by(desc(Token.time_created))
            .first()
        )
        if token:
            token.access_token = new_access_token
            token.refresh_token = new_refresh_token
            token.time_updated = datetime.datetime.now(datetime.UTC).isoformat()
            db.add(token)
            db.commit()
            db.refresh(token)
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
        }
    except HTTPException:
        raise
    except Exception as e:
        State.logger.error(f"An error occured while refreshing token: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occured while refreshing token: {str(e)}")


@router.post("/logout")
@token_required
async def logout_user(
    dependencies=Depends(JWTBearer()),
    db=Depends(get_db),
):
    try:
        user_id = decodeJWT(dependencies)["sub"]
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            State.logger.error("User not found")
            raise HTTPException(status_code=404, detail="User not found")
        token = (
            db.query(Token)
            .filter_by(user_id=user_id, access_token=dependencies, status=True)
            .order_by(desc(Token.time_created))
            .first()
        )
        if token:
            token.status = False
            token.time_updated = datetime.datetime.now(datetime.UTC).isoformat()
            db.add(token)
            db.commit()
            db.refresh(token)
        return {"message": "User logged out successfully"}
    except HTTPException:
        raise
    except Exception as e:
        State.logger.error(f"An error occured while logout: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occured while logout: {str(e)}")
