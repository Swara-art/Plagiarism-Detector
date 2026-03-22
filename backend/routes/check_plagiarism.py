from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.database.chroma_client import collection
from .upload_routes import extract_text, chunk_text
router = APIRouter()


@router.post("/check-plagiarism")
async def check_plagiarism(file: UploadFile = File(...)):
    file_bytes = await file.read()
    filename = file.filename

    try:
        text = extract_text(file_bytes, filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="No text could be extracted from the file")

    chunks = chunk_text(text)

    if not chunks:
        raise HTTPException(status_code=400, detail="No chunks could be created from extracted text")

    similarities = []
    source_scores = {}

    for chunk in chunks:
        results = collection.query(
            query_texts=[chunk],
            n_results=3
        )

        result_distances = results.get("distances", [[]])[0]
        result_metadatas = results.get("metadatas", [[]])[0]
        result_documents = results.get("documents", [[]])[0]

        for distance, metadata, matched_doc in zip(result_distances, result_metadatas, result_documents):
            similarity = max(0.0, 1 - distance)
            similarities.append(similarity)

            source_name = metadata.get("source", "Unknown")
            document_id = metadata.get("document_id", None)

            if source_name not in source_scores:
                source_scores[source_name] = {
                    "source_document": source_name,
                    "document_id": document_id,
                    "max_similarity": similarity,
                    "matched_chunks": 1,
                    "sample_text": matched_doc[:200] if matched_doc else ""
                }
            else:
                source_scores[source_name]["max_similarity"] = max(
                    source_scores[source_name]["max_similarity"],
                    similarity
                )
                source_scores[source_name]["matched_chunks"] += 1

    if not similarities:
        return {
            "filename": filename,
            "plagiarism_score": 0.0,
            "originality_score": 100.0,
            "matched_sources": []
        }

    avg_similarity = sum(similarities) / len(similarities)
    plagiarism_score = round(avg_similarity * 100, 2)
    originality_score = round(100 - plagiarism_score, 2)

    matched_sources = []
    for source_data in source_scores.values():
        matched_sources.append({
            "source_document": source_data["source_document"],
            "document_id": source_data["document_id"],
            "similarity": round(source_data["max_similarity"], 2),
            "matched_chunks": source_data["matched_chunks"],
            "sample_text": source_data["sample_text"]
        })

    matched_sources.sort(key=lambda x: x["similarity"], reverse=True)

    return {
        "filename": filename,
        "plagiarism_score": plagiarism_score,
        "originality_score": originality_score,
        "matched_sources": matched_sources[:5]
    }