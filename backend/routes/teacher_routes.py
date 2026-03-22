from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from backend.routes.upload_routes import extract_text
from backend.services.similarity_service import check_text_similarity
from backend.services.code_similarity_service import check_code_similarity
from backend.services.scoring_engine import compute_plagiarism_score, get_flagged_sections
from backend.services.code_preprocessing import structural_similarity
import uuid

router = APIRouter()

@router.post("/batch/upload")
async def teacher_batch_upload(files: List[UploadFile] = File(...)):
    if len(files) < 2:  raise HTTPException(400, "Upload at least 2 files.")
    if len(files) > 30: raise HTTPException(400, "Maximum 30 files per batch.")

    results, texts = [], {}
    for file in files:
        file_bytes = await file.read()
        try:    text = extract_text(file_bytes, file.filename)
        except ValueError:
            results.append({"filename": file.filename, "error": "Unsupported file type",
                             "plagiarism_score": None}); continue
        if not text or len(text.strip()) < 30:
            results.append({"filename": file.filename, "error": "No extractable text",
                             "plagiarism_score": None}); continue
        texts[file.filename] = text
        sim    = check_text_similarity(text)
        scores = compute_plagiarism_score(sim["all_similarities"])
        results.append({
            "filename": file.filename, "submission_id": str(uuid.uuid4())[:8],
            "plagiarism_score": scores["plagiarism_score"],
            "originality_score": scores["originality_score"],
            "verdict": scores["verdict"],
            "flagged_count": len(get_flagged_sections(sim["chunks"]))
        })

    filenames = list(texts.keys())
    matrix = []
    for i, fn1 in enumerate(filenames):
        for j, fn2 in enumerate(filenames):
            if j <= i: continue
            sim = _overlap(texts[fn1], texts[fn2])
            if sim >= 0.35:
                matrix.append({"file_a": fn1, "file_b": fn2,
                                "similarity": round(sim*100, 1), "flag": sim >= 0.60})
    matrix.sort(key=lambda x: x["similarity"], reverse=True)

    return {"total_files": len(files), "analysed": len(results), "results": results,
            "pairwise_similarities": matrix[:20],
            "high_risk_pairs": [m for m in matrix if m["flag"]]}

@router.post("/compare")
async def teacher_compare_two(file_a: UploadFile = File(...), file_b: UploadFile = File(...)):
    bytes_a, bytes_b = await file_a.read(), await file_b.read()
    try:
        text_a = extract_text(bytes_a, file_a.filename)
        text_b = extract_text(bytes_b, file_b.filename)
    except ValueError as e:
        raise HTTPException(400, str(e))
    sim   = _overlap(text_a, text_b)
    ra    = check_text_similarity(text_a)
    rb    = check_text_similarity(text_b)
    return {"file_a": file_a.filename, "file_b": file_b.filename,
            "overall_similarity": round(sim*100, 1), "verdict": _verdict(sim),
            "flagged_in_a": get_flagged_sections(ra["chunks"], 0.40)[:10],
            "flagged_in_b": get_flagged_sections(rb["chunks"], 0.40)[:10],
            "preview_a": text_a[:800], "preview_b": text_b[:800]}

@router.post("/compare/code")
async def teacher_compare_code(file_a: UploadFile = File(...), file_b: UploadFile = File(...)):
    code_a = (await file_a.read()).decode("utf-8", errors="ignore")
    code_b = (await file_b.read()).decode("utf-8", errors="ignore")
    sim    = structural_similarity(code_a, code_b)
    ra     = check_code_similarity(code_a)
    rb     = check_code_similarity(code_b)
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

