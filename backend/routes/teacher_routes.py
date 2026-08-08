from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
import logging
import os
from backend.auth.jwt_handler import require_role
from backend.database.postgres import User
from backend.services.text_preprocessing import extract_text
from backend.services.similarity_service import check_text_similarity
from backend.services.code_similarity_service import check_code_similarity
from backend.services.scoring_engine import compute_plagiarism_score, get_flagged_sections
from backend.services.code_preprocessing import structural_similarity

logger = logging.getLogger("teacher_routes")
router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB per file

@router.post("/batch/upload")
async def teacher_batch_upload(files: List[UploadFile] = File(...), user: User = Depends(require_role("teacher"))):
    if len(files) < 2:  raise HTTPException(400, "Upload at least 2 files.")
    if len(files) > 15: raise HTTPException(400, "Maximum 15 files per batch for comparison.")

    results, texts = [], {}
    for file in files:
        # Check size cap before loading
        file_bytes = await file.read(MAX_FILE_SIZE + 1)
        if len(file_bytes) > MAX_FILE_SIZE:
            results.append({
                "filename": file.filename, 
                "error": "File too large (Max 10MB)",
                "plagiarism_score": None
            })
            continue

        try:
            text = extract_text(file_bytes, file.filename)
        except ValueError as e:
            results.append({
                "filename": file.filename, 
                "error": str(e),
                "plagiarism_score": None
            })
            continue
        except Exception as e:
            logger.exception("Text extraction failed for batch file %s: %s", file.filename, e)
            results.append({
                "filename": file.filename, 
                "error": "Failed to extract text",
                "plagiarism_score": None
            })
            continue

        if not text or len(text.strip()) < 30:
            results.append({
                "filename": file.filename, 
                "error": "No extractable text (too short)",
                "plagiarism_score": None
            })
            continue

        texts[file.filename] = text
        try:
            # Performs the real-time internet query similarity scoring
            sim = check_text_similarity(text)
            scores = compute_plagiarism_score(sim["all_similarities"])
            results.append({
                "filename": file.filename,
                "plagiarism_score": scores["plagiarism_score"],
                "originality_score": scores["originality_score"],
                "verdict": scores["verdict"],
                "flagged_count": len(get_flagged_sections(sim["chunks"]))
            })
        except Exception as e:
            logger.exception("Error checking similarity for batch file %s: %s", file.filename, e)
            results.append({
                "filename": file.filename,
                "error": f"Similarity check failed: {str(e)}",
                "plagiarism_score": None
            })

    # Pairwise comparison calculations between all uploaded files
    filenames = list(texts.keys())
    matrix = []
    for i, fn1 in enumerate(filenames):
        for j, fn2 in enumerate(filenames):
            if j <= i: continue
            
            # Determine if both are code files
            ext1 = os.path.splitext(fn1)[1].lower()
            ext2 = os.path.splitext(fn2)[1].lower()
            is_code = ext1 in (".py", ".js", ".java", ".c", ".cpp", ".ts", ".go", ".rs") and ext2 in (".py", ".js", ".java", ".c", ".cpp", ".ts", ".go", ".rs")
            
            if is_code:
                # Use AST structural comparison
                lang = "python"
                if ext1 in (".js", ".ts"): lang = "javascript"
                elif ext1 in (".cpp", ".c++", ".c"): lang = "cpp"
                elif ext1 == ".java": lang = "java"
                elif ext1 == ".go": lang = "go"
                elif ext1 == ".rs": lang = "rust"
                sim = structural_similarity(texts[fn1], texts[fn2], lang)
            else:
                # Use generic overlap comparison
                sim = _overlap(texts[fn1], texts[fn2])
                
            if sim >= 0.35:
                matrix.append({
                    "file_a": fn1, "file_b": fn2,
                    "similarity": round(sim*100, 1), "flag": sim >= 0.60
                })
    matrix.sort(key=lambda x: x["similarity"], reverse=True)

    return {"total_files": len(files), "analysed": len(results), "results": results,
            "pairwise_similarities": matrix[:20],
            "high_risk_pairs": [m for m in matrix if m["flag"]]}

@router.post("/compare")
async def teacher_compare_two(file_a: UploadFile = File(...), file_b: UploadFile = File(...), user: User = Depends(require_role("teacher"))):
    bytes_a = await file_a.read(MAX_FILE_SIZE + 1)
    bytes_b = await file_b.read(MAX_FILE_SIZE + 1)
    
    if len(bytes_a) > MAX_FILE_SIZE or len(bytes_b) > MAX_FILE_SIZE:
        raise HTTPException(413, "One of the files is too large. Limit is 10MB per file.")

    try:
        text_a = extract_text(bytes_a, file_a.filename)
        text_b = extract_text(bytes_b, file_b.filename)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.exception("Text extraction error during pairwise comparison: %s", e)
        raise HTTPException(422, f"Failed to extract text: {str(e)}")

    sim   = _overlap(text_a, text_b)
    ra    = check_text_similarity(text_a)
    rb    = check_text_similarity(text_b)
    return {"file_a": file_a.filename, "file_b": file_b.filename,
            "overall_similarity": round(sim*100, 1), "verdict": _verdict(sim),
            "flagged_in_a": get_flagged_sections(ra["chunks"], 0.40)[:10],
            "flagged_in_b": get_flagged_sections(rb["chunks"], 0.40)[:10],
            "preview_a": text_a[:800], "preview_b": text_b[:800]}

@router.post("/compare/code")
async def teacher_compare_code(file_a: UploadFile = File(...), file_b: UploadFile = File(...), user: User = Depends(require_role("teacher"))):
    bytes_a = await file_a.read(MAX_FILE_SIZE + 1)
    bytes_b = await file_b.read(MAX_FILE_SIZE + 1)

    if len(bytes_a) > MAX_FILE_SIZE or len(bytes_b) > MAX_FILE_SIZE:
        raise HTTPException(413, "One of the files is too large. Limit is 10MB per file.")

    code_a = bytes_a.decode("utf-8", errors="ignore")
    code_b = bytes_b.decode("utf-8", errors="ignore")
    
    ext = os.path.splitext(file_a.filename)[1].lower()
    lang = "python"
    if ext in (".js", ".ts"): lang = "javascript"
    elif ext in (".cpp", ".c++", ".c"): lang = "cpp"
    elif ext == ".java": lang = "java"
    elif ext == ".go": lang = "go"
    elif ext == ".rs": lang = "rust"

    sim    = structural_similarity(code_a, code_b, lang)
    ra     = check_code_similarity(code_a, lang)
    rb     = check_code_similarity(code_b, lang)
    return {"file_a": file_a.filename, "file_b": file_b.filename,
            "structural_similarity": round(sim*100, 1), "verdict": _verdict(sim),
            "flagged_blocks_a": ra["flagged_blocks"][:5],
            "flagged_blocks_b": rb["flagged_blocks"][:5],
            "functions_in_a": ra["functions_analysed"],
            "functions_in_b": rb["functions_analysed"],
            "preview_a": code_a[:600], "preview_b": code_b[:600]}

def _overlap(a: str, b: str) -> float:
    wa, wb = set(a.lower().split()), set(b.lower().split())
    if not wa or not wb: return 0.0
    return len(wa & wb) / len(wa | wb)

def _verdict(sim: float) -> str:
    if sim >= 0.75: return "⚠️ Very High Similarity — Likely Copied"
    if sim >= 0.55: return "🟠 High Similarity — Probable Copying"
    if sim >= 0.35: return "🟡 Moderate Similarity — Review Needed"
    return "🟢 Low Similarity — Likely Independent Work"
