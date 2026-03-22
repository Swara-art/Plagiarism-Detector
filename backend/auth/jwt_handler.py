import os
from datetime import datetime, timedelta
from typing import Optional

try:
    from jose import JWTError, jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

SECRET_KEY = os.getenv("JWT_SECRET", "plagiarism-detector-secret-change-in-prod")
ALGORITHM  = "HS256"
EXPIRE_MIN = 60 * 8

# Demo users — plain-text comparison as fallback (dev/demo only)
DEMO_USERS = {
    "student1": {"username": "student1", "plain_password": "student123",
                 "role": "student", "full_name": "Demo Student"},
    "teacher1": {"username": "teacher1", "plain_password": "teacher123",
                 "role": "teacher", "full_name": "Demo Teacher"},
}

def authenticate_user(username: str, password: str, role: str) -> Optional[dict]:
    user = DEMO_USERS.get(username)
    if not user or user["role"] != role:
        return None
    if password != user["plain_password"]:
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    if not JWT_AVAILABLE:
        return "no-auth-token"
    payload = {
        **data,
        "exp": datetime.utcnow() + (expires_delta or timedelta(minutes=EXPIRE_MIN))
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    if not JWT_AVAILABLE:
        return None
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None