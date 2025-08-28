import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc

from core.auth import JWTBearer, decodeJWT, token_required
from database.database import get_db
from models.token import Token
from models.user import User

router = APIRouter()


@router.get("/")
async def get_users(
    db=Depends(get_db),
):
    try:
        users = db.query(User).all()
        for user in users:
            del user.password
        return {"users": [user.__dict__ for user in users]}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occured while fetching all users: {str(e)}",
        )


@router.get("/me")
@token_required
async def get_self(
    dependencies=Depends(JWTBearer()),
    db=Depends(get_db),
):
    try:
        user_id = decodeJWT(dependencies)["sub"]["user_id"]
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        del user.password
        return {"user": user.__dict__}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occured while fetching user details: {str(e)}",
        )


@router.get("/{user_id}")
@token_required
async def get_user(
    user_id: str,
    dependencies=Depends(JWTBearer()),
    db=Depends(get_db),
):
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        del user.password
        return {"user": user.__dict__}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occured while fetching user details: {str(e)}",
        )


@router.put("/")
@token_required
async def update_user(
    dependencies=Depends(JWTBearer()),
    name: str = Query(None, description=""),
    email: str = Query(None, description=""),
    phone: str = Query(None, description=""),
    role: str = Query(None, description=""),
    db=Depends(get_db),
):
    try:
        user_id = decodeJWT(dependencies)["sub"]["user_id"]
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user_with_email = db.query(User).filter(User.email == email).first()
        if user_with_email and user_with_email.user_id != user_id:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.name = name
        user.email = email
        user.phone = phone
        user.role = role
        user.time_updated = datetime.datetime.now(datetime.UTC).isoformat()
        db.add(user)
        db.commit()
        db.refresh(user)
        return {"message": "User updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occured while updating user details: {str(e)}",
        )


@router.delete("/")
@token_required
async def delete_user(
    dependencies=Depends(JWTBearer()),
    db=Depends(get_db),
):
    try:
        user_id = decodeJWT(dependencies)["sub"]["user_id"]
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        db.delete(user)
        db.commit()
        db.refresh(user)
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
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An error occured while deleting user: {str(e)}"
        )
