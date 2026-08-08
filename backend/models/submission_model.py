from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class TextSubmission(BaseModel):
    submission_id: Optional[str] = None
    content: str
    mode: Optional[str] = "semantic"

class CodeSubmission(BaseModel):
    submission_id: Optional[str] = None
    code: str
    language: Optional[str] = "python"

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)

class UserRegistration(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    username: str = Field(min_length=3, max_length=150, pattern=r"^[A-Za-z0-9_.-]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str
