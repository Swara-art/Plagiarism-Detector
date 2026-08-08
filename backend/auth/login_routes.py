from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.auth.jwt_handler import create_access_token, get_current_user, hash_password, verify_password
from backend.database.postgres import User, get_db
from backend.models.submission_model import UserLogin, UserRegistration

router = APIRouter()

@router.get("/me")
def current_user(user: User = Depends(get_current_user)):
    return {"id": str(user.id), "role": user.role, "full_name": user.full_name, "username": user.username, "email": user.email}

@router.post("/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(credentials.email).lower()).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This email is not registered. Register first.")
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password is incorrect.")
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    token = create_access_token(user)
    return {"access_token": token, "token_type": "bearer",
            "role": user.role, "full_name": user.full_name,
            "username": user.username}

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(credentials: UserRegistration, db: Session = Depends(get_db)):
    if credentials.role not in {"student", "teacher"}:
        raise HTTPException(status_code=400, detail="Role must be student or teacher.")
    duplicate = db.query(User).filter(or_(User.email == str(credentials.email).lower(), User.username == credentials.username)).first()
    if duplicate:
        field = "email" if duplicate.email.lower() == str(credentials.email).lower() else "username"
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"That {field} is already registered.")
    user = User(full_name=credentials.full_name, username=credentials.username, email=str(credentials.email).lower(), password_hash=hash_password(credentials.password), role=credentials.role)
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email or username is already registered.") from exc
    db.refresh(user)
    return {"access_token": create_access_token(user), "token_type": "bearer", "role": user.role, "full_name": user.full_name, "username": user.username}
