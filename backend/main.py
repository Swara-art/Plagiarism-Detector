import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.student_routes import router as student_router
from backend.routes.teacher_routes import router as teacher_router
from backend.auth.login_routes import router as auth_router
import uvicorn
from backend.database.postgres import Base, engine

# Automatically create tables in PostgreSQL on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Plagiarism Detector API",
    description="AI-powered plagiarism detection — text, code, and handwriting",
    version="2.0.0"
)

# Secure CORS configuration - restrict to specific development origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router,       prefix="/auth",       tags=["Auth"])
app.include_router(student_router,    prefix="/student",    tags=["Student"])
app.include_router(teacher_router,    prefix="/teacher",    tags=["Teacher"])

@app.get("/")
def read_root():
    return {
        "message": "Plagiarism Detector API v2.0",
        "docs": "/docs",
        "endpoints": {
            "auth":    "/auth/login",
            "student": "/student/check/text | /student/check/file | /student/check/code | /student/check/handwritten",
            "teacher": "/teacher/batch/upload | /teacher/compare | /teacher/compare/code"
        }
    }

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
