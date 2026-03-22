from typing import List

def compute_plagiarism_score(all_similarities: List[float]) -> dict:
    if not all_similarities:
        return {"plagiarism_score": 0.0, "originality_score": 100.0,
                "verdict": "Original", "confidence": "High"}

    sorted_sims = sorted(all_similarities, reverse=True)
    n           = len(sorted_sims)
    top_count   = max(1, n // 3)
    top_avg     = sum(sorted_sims[:top_count]) / top_count
    bottom_avg  = sum(sorted_sims[top_count:]) / max(1, n - top_count)
    weighted    = top_avg * 0.6 + bottom_avg * 0.4

    plag = round(weighted * 100, 2)
    orig = round(100 - plag, 2)

    if   plag >= 75: verdict, conf = "High Plagiarism Detected",    "High"
    elif plag >= 50: verdict, conf = "Likely Plagiarised",           "Medium"
    elif plag >= 30: verdict, conf = "Suspicious Similarities Found","Medium"
    else:            verdict, conf = "Mostly Original",              "High"

    return {"plagiarism_score": plag, "originality_score": orig,
            "verdict": verdict, "confidence": conf}

def get_flagged_sections(chunk_results: list, threshold: float = 0.45) -> list:
    flagged = [
        {
            "start": c["start"], "end": c["end"],
            "match_score": c["best_similarity"],
            "matched_source": c["best_source"],
            "matched_text": c.get("matched_text", ""),
            "reason": _reason(c["best_similarity"])
        }
        for c in chunk_results
        if c.get("best_similarity", 0.0) >= threshold and c.get("best_source")
    ]
    return sorted(flagged, key=lambda x: x["match_score"], reverse=True)

def _reason(sim: float) -> str:
    if sim >= 0.90: return "Near-identical content detected — possibly direct copy-paste."
    if sim >= 0.75: return "Very high semantic similarity — likely paraphrased from this source."
    if sim >= 0.60: return "High semantic overlap — significant content reuse detected."
    return "Moderate similarity — possible partial reuse or paraphrasing."