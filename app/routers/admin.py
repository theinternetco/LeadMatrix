from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models import User
from app.routers.auth import get_current_user, hash_password

router = APIRouter(redirect_slashes=False)

ADMIN_EMAILS = {"abhishek@theinternetcompany.in", "zishan@theinternetcompany.in"}
ALLOWED_DOMAIN = "theinternetcompany.in"


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


class CreateUserRequest(BaseModel):
    email: str
    full_name: Optional[str] = None
    password: str


@router.get("/users")
def list_users(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.created_at).all()
    return [
        {
            "id":         u.id,
            "email":      u.email,
            "full_name":  u.full_name,
            "is_active":  u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login": u.last_login.isoformat() if u.last_login else None,
        }
        for u in users
    ]


@router.post("/users", status_code=201)
def create_user(
    payload: CreateUserRequest,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    email = payload.email.lower().strip()

    if not email.endswith(f"@{ALLOWED_DOMAIN}"):
        raise HTTPException(status_code=400, detail=f"Only @{ALLOWED_DOMAIN} emails are allowed")

    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="A user with that email already exists")

    user = User(
        email=email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id":        user.id,
        "email":     user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
    }


@router.delete("/users/{user_id}", status_code=200)
def delete_user(
    user_id: int,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if user_id == current_admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"message": f"User {user.email} deleted"}
