from pydantic import BaseModel
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
    username: str
    password: str
    role: str  # "student" or "teacher"