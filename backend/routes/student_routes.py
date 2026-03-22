from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.models.submission_model import TextSubmission, CodeSubmission
from backend.services.similarity_service import check_text_similarity
from backend.services.code_similarity_service import check_code_similarity
from backend.services.scoring_engine import compute_plagiarism_score, get_flagged_sections
from backend.services.explanation_service import build_full_report
from backend.services.handwriting_ocr import extract_text_from_image
from backend.routes.upload_routes import extract_text
import uuid

router = APIRouter()

@router.post("/check/text")
async def student_check_text(submission: TextSubmission):
    if not submission.content or len(submission.content.strip()) < 50:
        raise HTTPException(400, "Content too short. Minimum 50 characters.")
    sid     = submission.submission_id or str(uuid.uuid4())[:8]
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
    return report

@router.post("/check/file")
async def student_check_file(file: UploadFile = File(...)):
    file_bytes = await file.read()
    try:
        text = extract_text(file_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not text or len(text.strip()) < 50:
        raise HTTPException(400, "Could not extract enough text from file.")
    sid     = str(uuid.uuid4())[:8]
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
    return report

@router.post("/check/code")
async def student_check_code(submission: CodeSubmission):
    if not submission.code or len(submission.code.strip()) < 20:
        raise HTTPException(400, "Code too short. Minimum 20 characters.")
    sid     = submission.submission_id or str(uuid.uuid4())[:8]
    results = check_code_similarity(submission.code, submission.language)
    scores  = compute_plagiarism_score(results["all_similarities"])
    sources = sorted(results["source_scores"].values(),
                     key=lambda x: x["max_similarity"], reverse=True)
    return {
        "submission_id": sid, "language": submission.language,
        "plagiarism_score": scores["plagiarism_score"],
        "originality_score": scores["originality_score"],
        "verdict": scores["verdict"], "confidence": scores["confidence"],
        "flagged_blocks": results["flagged_blocks"],
        "matched_sources": list(sources)[:5],
        "functions_analysed": results["functions_analysed"],
        "summary": f"Analysed {results['functions_analysed']} function(s). {scores['verdict']}."
    }

@router.post("/check/handwritten")
async def student_check_handwritten(file: UploadFile = File(...)):
    file_bytes = await file.read()
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("jpg","jpeg","png","bmp","tiff","webp"):
        raise HTTPException(400, "Unsupported image format. Use JPG, PNG, or TIFF.")
    ocr = extract_text_from_image(file_bytes)
    if not ocr["success"]:
        raise HTTPException(422, ocr["error"])
    sid     = str(uuid.uuid4())[:8]
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
    return report