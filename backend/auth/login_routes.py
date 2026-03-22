from fastapi import APIRouter, HTTPException
from backend.models.submission_model import UserLogin
from backend.auth.jwt_handler import authenticate_user, create_access_token

router = APIRouter()

@router.post("/login")
def login(credentials: UserLogin):
    user = authenticate_user(credentials.username, credentials.password, credentials.role)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username, password, or role.")
    token = create_access_token({"sub": user["username"], "role": user["role"],
                                  "full_name": user["full_name"]})
    return {"access_token": token, "token_type": "bearer",
            "role": user["role"], "full_name": user["full_name"],
            "username": user["username"]}

@router.get("/demo-credentials")
def demo_credentials():
    return {
        "student": {"username": "student1", "password": "student123", "role": "student"},
        "teacher": {"username": "teacher1", "password": "teacher123", "role": "teacher"}
    }