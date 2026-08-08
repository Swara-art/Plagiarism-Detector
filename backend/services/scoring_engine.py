from typing import List

def compute_plagiarism_score(all_similarities: List[float]) -> dict:
    """
    Computes a composite plagiarism score based on all similarities calculated for individual chunks.
    
    Calibration Heuristic:
    - Simply averaging all similarities dilutes cases where a student copies large blocks
      but writes some original wrapping text.
    - Sorting similarities and separating them into the top 1/3 (highest similarities) and
      the remaining bottom 2/3 lets us highlight intense matching areas.
    - We weight the top 1/3 at 60% (0.6) and the bottom 2/3 at 40% (0.4) to emphasize
      highly-copied blocks without completely ignoring the rest of the text.
    """
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

    # Thresholds are selected based on typical university plagiarism review standards:
    # >= 75% similarity is flagrant plagiarism, 50-75% is substantial copying, 30-50% is suspicious
    if   plag >= 75: verdict, conf = "High Plagiarism Detected",    "High"
    elif plag >= 50: verdict, conf = "Likely Plagiarised",           "Medium"
    elif plag >= 30: verdict, conf = "Suspicious Similarities Found","Medium"
    else:            verdict, conf = "Mostly Original",              "High"

    return {"plagiarism_score": plag, "originality_score": orig,
            "verdict": verdict, "confidence": conf}

def get_flagged_sections(chunk_results: list, threshold: float = 0.45) -> list:
    """
    Filters chunk comparison results to return only those exceeding the similarity threshold.
    
    A default threshold of 0.45 Jaccard/Cosine similarity indicates that more than ~45% of
    the semantic context/vocabulary overlaps, which is standard for raising a plagiarism flag.
    """
    flagged = [
        {
            "start": c["start"], "end": c["end"],
            "match_score": c["best_similarity"],
            "matched_source": c["best_source"],
            "url": c.get("url", ""),
            "matched_text": c.get("matched_text", ""),
            "reason": _reason(c["best_similarity"])
        }
        for c in chunk_results
        if c.get("best_similarity", 0.0) >= threshold and c.get("best_source")
    ]
    return sorted(flagged, key=lambda x: x["match_score"], reverse=True)

def _reason(sim: float) -> str:
    """
    Returns a human-readable explanation based on similarity thresholds.
    """
    if sim >= 0.90: return "Near-identical content detected — possibly direct copy-paste."
    if sim >= 0.75: return "Very high semantic similarity — likely paraphrased from this source."
    if sim >= 0.60: return "High semantic overlap — significant content reuse detected."
    return "Moderate similarity — possible partial reuse or paraphrasing."