from backend.database.chroma_client import collection
from backend.services.text_preprocessing import chunk_with_metadata

def check_text_similarity(text: str, n_results: int = 3) -> dict:
    chunks = chunk_with_metadata(text, chunk_size=500, overlap=100)
    if not chunks:
        return {"chunks": [], "source_scores": {}, "all_similarities": []}

    all_similarities = []
    source_scores = {}
    chunk_results = []

    for chunk_info in chunks:
        chunk_text = chunk_info["text"].strip()
        if len(chunk_text) < 30:
            continue
        try:
            results = collection.query(query_texts=[chunk_text], n_results=n_results)
        except Exception:
            continue

        distances  = results.get("distances",  [[]])[0]
        metadatas  = results.get("metadatas",  [[]])[0]
        documents  = results.get("documents",  [[]])[0]

        best_similarity, best_source, best_matched_text = 0.0, None, ""

        for distance, metadata, matched_doc in zip(distances, metadatas, documents):
            similarity  = max(0.0, 1.0 - distance)
            source_name = metadata.get("source", "Unknown")
            document_id = metadata.get("document_id", "")
            all_similarities.append(similarity)

            if similarity > best_similarity:
                best_similarity   = similarity
                best_source       = source_name
                best_matched_text = matched_doc[:300] if matched_doc else ""

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

        chunk_results.append({
            "start": chunk_info["start"], "end": chunk_info["end"],
            "text": chunk_text[:200], "best_similarity": round(best_similarity, 4),
            "best_source": best_source, "matched_text": best_matched_text
        })

    return {"chunks": chunk_results, "source_scores": source_scores, "all_similarities": all_similarities}