from datetime import datetime, timezone
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from backend.auth.jwt_handler import require_role
from backend.database.postgres import PlagiarismReport, Submission, SubmissionFile, User, get_db
from backend.models.submission_model import TextSubmission, CodeSubmission
from backend.services.similarity_service import check_text_similarity
from backend.services.code_similarity_service import check_code_similarity
from backend.services.scoring_engine import compute_plagiarism_score, get_flagged_sections
from backend.services.explanation_service import build_full_report
from backend.services.handwriting_ocr import extract_text_from_image
from backend.services.text_preprocessing import extract_text
from backend.services.code_preprocessing import SUPPORTED_LANGUAGES

logger = logging.getLogger("student_routes")
router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def create_submission(db: Session, user: User, title: str, submission_type: str, content: str | None = None, language: str | None = None) -> Submission:
    record = Submission(submitted_by=user.id, title=title, submission_type=submission_type, pasted_content=content, language=language, status="processing", processing_started_at=datetime.now(timezone.utc))
    db.add(record)
    db.flush()
    return record

def save_report(db: Session, record: Submission, scores: dict, summary: str, chunks: int | None = None) -> None:
    score = float(scores["plagiarism_score"])
    verdict = "very_high_similarity" if score >= 75 else "high_similarity" if score >= 55 else "moderate_similarity" if score >= 35 else "low_similarity"
    db.add(PlagiarismReport(submission_id=record.id, plagiarism_score=score, originality_score=float(scores["originality_score"]), confidence_score=None, verdict=verdict, summary=summary, chunks_analysed=chunks))
    record.status = "completed"
    record.processing_completed_at = datetime.now(timezone.utc)
    db.commit()

@router.post("/check/text")
async def student_check_text(submission: TextSubmission, user: User = Depends(require_role("student")), db: Session = Depends(get_db)):
    if not submission.content or len(submission.content.strip()) < 50:
        raise HTTPException(400, "Content too short. Minimum 50 characters.")
    
    try:
        record = create_submission(db, user, "Text submission", "text", submission.content)
        sid = str(record.id)
        results = check_text_similarity(submission.content)
        scores  = compute_plagiarism_score(results["all_similarities"])
        flagged = get_flagged_sections(results["chunks"])
        sources = sorted(results["source_scores"].values(),
                         key=lambda x: x["max_similarity"], reverse=True)
        report  = build_full_report("text_submission", sid,
                                    scores["plagiarism_score"], scores["originality_score"],
                                    scores["verdict"], flagged, list(sources)[:5],
                                    len(results["chunks"]))
        report["confidence"] = scores["confidence"]
        save_report(db, record, scores, report["summary"], len(results["chunks"]))
        return report
    except Exception as e:
        logger.exception("Error checking text similarity for student: %s", e)
        raise HTTPException(500, f"An error occurred during text check: {str(e)}")

@router.post("/check/file")
async def student_check_file(file: UploadFile = File(...), user: User = Depends(require_role("student")), db: Session = Depends(get_db)):
    # Memory-safe file reading with size limit validation
    file_bytes = await file.read(MAX_FILE_SIZE + 1)
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large. Maximum size allowed is 10MB.")
        
    try:
        text = extract_text(file_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.exception("Text extraction error: %s", e)
        raise HTTPException(422, f"Failed to extract text: {str(e)}")

    if not text or len(text.strip()) < 50:
        raise HTTPException(400, "Could not extract enough text from file.")
        
    try:
        record = create_submission(db, user, file.filename, "document")
        db.add(SubmissionFile(submission_id=record.id, original_filename=file.filename, mime_type=file.content_type, file_size_bytes=len(file_bytes), extracted_text=text))
        sid = str(record.id)
        results = check_text_similarity(text)
        scores  = compute_plagiarism_score(results["all_similarities"])
        flagged = get_flagged_sections(results["chunks"])
        sources = sorted(results["source_scores"].values(),
                         key=lambda x: x["max_similarity"], reverse=True)
        report  = build_full_report(file.filename, sid,
                                    scores["plagiarism_score"], scores["originality_score"],
                                    scores["verdict"], flagged, list(sources)[:5],
                                    len(results["chunks"]))
        report["confidence"] = scores["confidence"]
        save_report(db, record, scores, report["summary"], len(results["chunks"]))
        return report
    except Exception as e:
        logger.exception("Error during file analysis: %s", e)
        raise HTTPException(500, f"Analysis failed: {str(e)}")

@router.post("/check/code")
async def student_check_code(submission: CodeSubmission, user: User = Depends(require_role("student")), db: Session = Depends(get_db)):
    if not submission.code or len(submission.code.strip()) < 20:
        raise HTTPException(400, "Code too short. Minimum 20 characters.")
        
    lang = (submission.language or "python").lower()
    if lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(400, f"Unsupported language: '{submission.language}'. Supported languages: {', '.join(SUPPORTED_LANGUAGES.keys())}")
        
    try:
        record = create_submission(db, user, "Code submission", "code", submission.code, submission.language)
        sid = str(record.id)
        results = check_code_similarity(submission.code, submission.language)
        scores  = compute_plagiarism_score(results["all_similarities"])
        sources = sorted(results["source_scores"].values(),
                         key=lambda x: x["max_similarity"], reverse=True)
        report = {
            "submission_id": sid, "language": submission.language,
            "plagiarism_score": scores["plagiarism_score"],
            "originality_score": scores["originality_score"],
            "verdict": scores["verdict"], "confidence": scores["confidence"],
            "flagged_blocks": results["flagged_blocks"],
            "matched_sources": list(sources)[:5],
            "functions_analysed": results["functions_analysed"],
            "summary": f"Analysed {results['functions_analysed']} function(s). {scores['verdict']}."
        }
        save_report(db, record, scores, report["summary"])
        return report
    except Exception as e:
        logger.exception("Error analyzing code submission: %s", e)
        raise HTTPException(500, f"Code analysis failed: {str(e)}")

@router.post("/check/handwritten")
async def student_check_handwritten(file: UploadFile = File(...), user: User = Depends(require_role("student")), db: Session = Depends(get_db)):
    # MIME validation
    if not file.content_type.startswith("image/"):
         raise HTTPException(400, f"Unsupported format. Expected image file, got: {file.content_type}")
         
    file_bytes = await file.read(MAX_FILE_SIZE + 1)
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(413, "Image file too large. Maximum size allowed is 10MB.")
        
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("jpg","jpeg","png","bmp","tiff","webp"):
        raise HTTPException(400, "Unsupported image format. Use JPG, PNG, WEBP, or TIFF.")
        
    try:
        ocr = extract_text_from_image(file_bytes)
        if not ocr["success"]:
            raise HTTPException(422, ocr["error"])
            
        record = create_submission(db, user, file.filename, "handwritten")
        db.add(SubmissionFile(submission_id=record.id, original_filename=file.filename, mime_type=file.content_type, file_size_bytes=len(file_bytes), extracted_text=ocr["text"]))
        sid = str(record.id)
        results = check_text_similarity(ocr["text"])
        scores  = compute_plagiarism_score(results["all_similarities"])
        flagged = get_flagged_sections(results["chunks"])
        sources = sorted(results["source_scores"].values(),
                         key=lambda x: x["max_similarity"], reverse=True)
        report  = build_full_report(file.filename, sid,
                                    scores["plagiarism_score"], scores["originality_score"],
                                    scores["verdict"], flagged, list(sources)[:5],
                                    len(results["chunks"]))
        report["extracted_text"]  = ocr["text"][:500]
        report["ocr_word_count"]  = ocr["word_count"]
        report["confidence"]      = scores["confidence"]
        save_report(db, record, scores, report["summary"], len(results["chunks"]))
        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Handwriting OCR check failed: %s", e)
        raise HTTPException(500, f"OCR Plagiarism analysis failed: {str(e)}")
