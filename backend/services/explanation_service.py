from typing import List

WIKIPEDIA_TOPICS = {
    "Artificial intelligence", "Machine learning", "Deep learning",
    "Computer vision", "Natural language processing", "Reinforcement learning"
}

def generate_citation_suggestions(matched_sources: list) -> List[str]:
    citations = []
    for source in matched_sources:
        name   = source.get("source_document", "Unknown Source")
        doc_id = source.get("document_id", "")
        if source.get("type") == "wikipedia" or name in WIKIPEDIA_TOPICS:
            citations.append(
                f'Wikipedia contributors. "{name}." Wikipedia, The Free Encyclopedia. '
                f'Retrieved from https://en.wikipedia.org/wiki/{name.replace(" ", "_")}'
            )
        else:
            citations.append(
                f'Author(s). "{name}" [Document ID: {doc_id[:8] if doc_id else "N/A"}]. '
                f'Submitted work. Cite appropriately if referencing.'
            )
    return citations

def generate_summary(plag: float, flagged: int, total: int) -> str:
    if plag >= 75:
        return (f"This submission shows significant plagiarism ({plag:.1f}% similarity). "
                f"{flagged} of {total} sections were flagged. Immediate review required.")
    if plag >= 50:
        return (f"This submission contains notable similarities ({plag:.1f}%). "
                f"{flagged} sections flagged. Review and add citations where needed.")
    if plag >= 30:
        return (f"Some suspicious similarities found ({plag:.1f}%). "
                f"{flagged} sections raised concerns. Review flagged sections for attribution.")
    return (f"Submission appears largely original ({100-plag:.1f}% original). "
            f"Only {flagged} minor similarities detected. No significant concerns found.")

def build_full_report(filename, submission_id, plagiarism_score, originality_score,
                      verdict, flagged_sections, matched_sources, total_chunks) -> dict:
    return {
        "submission_id": submission_id, "filename": filename,
        "plagiarism_score": plagiarism_score, "originality_score": originality_score,
        "verdict": verdict, "flagged_sections": flagged_sections,
        "matched_sources": matched_sources[:5],
        "citations": generate_citation_suggestions(matched_sources),
        "summary": generate_summary(plagiarism_score, len(flagged_sections), total_chunks),
        "total_chunks_analysed": total_chunks, "flagged_count": len(flagged_sections)
    }