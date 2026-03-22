from backend.database.chroma_client import collection
from backend.services.code_preprocessing import (
    normalize_python_code, extract_ast_structure,
    structural_similarity, extract_functions
)

def check_code_similarity(code: str, language: str = "python") -> dict:
    normalized       = normalize_python_code(code)
    structure_tokens = extract_ast_structure(normalized)
    functions        = extract_functions(code)

    all_similarities = []
    source_scores    = {}

    # Whole-file check
    try:
        results   = collection.query(query_texts=[structure_tokens[:2000]], n_results=5)
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        documents = results.get("documents", [[]])[0]
        for distance, metadata, matched_doc in zip(distances, metadatas, documents):
            similarity  = max(0.0, 1.0 - distance)
            source_name = metadata.get("source", "Unknown")
            document_id = metadata.get("document_id", "")
            all_similarities.append(similarity)
            if source_name not in source_scores:
                source_scores[source_name] = {
                    "source_document": source_name, "document_id": document_id,
                    "max_similarity": similarity, "matched_chunks": 1,
                    "sample_text": matched_doc[:200] if matched_doc else ""
                }
            else:
                if similarity > source_scores[source_name]["max_similarity"]:
                    source_scores[source_name]["max_similarity"] = similarity
                source_scores[source_name]["matched_chunks"] += 1
    except Exception:
        pass

    # Function-level check
    flagged_blocks = []
    for func in functions:
        if not func["structure"].strip(): continue
        try:
            results   = collection.query(query_texts=[func["structure"][:1000]], n_results=3)
            distances = results.get("distances", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            for distance, metadata in zip(distances, metadatas):
                similarity  = max(0.0, 1.0 - distance)
                source_name = metadata.get("source", "Unknown")
                all_similarities.append(similarity)
                if similarity >= 0.45:
                    flagged_blocks.append({
                        "lines": f"{func['start_line']}-{func['end_line']}",
                        "function_name": func["name"],
                        "match_score": round(similarity, 4),
                        "matched_source": source_name,
                        "reason": _code_reason(similarity)
                    })
                    break
        except Exception:
            continue

    return {
        "flagged_blocks": sorted(flagged_blocks, key=lambda x: x["match_score"], reverse=True),
        "source_scores": source_scores,
        "all_similarities": all_similarities,
        "functions_analysed": len(functions)
    }

def _code_reason(sim: float) -> str:
    if sim >= 0.90: return "Identical AST structure — likely direct copy with variable renaming."
    if sim >= 0.75: return "Very similar logical structure — probable code reuse or heavy adaptation."
    if sim >= 0.60: return "Significant structural overlap — similar algorithm or pattern detected."
    return "Moderate structural similarity — shared logic patterns found."