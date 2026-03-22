from chromadb.utils import embedding_functions
from backend.services.text_preprocessing import preprocess_for_embedding

_embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

def get_embedding(text: str) -> list:
    return _embedding_fn([preprocess_for_embedding(text)])[0]

def get_embeddings(texts: list) -> list:
    return _embedding_fn([preprocess_for_embedding(t) for t in texts])

def cosine_similarity(vec1: list, vec2: list) -> float:
    import math
    dot = sum(a * b for a, b in zip(vec1, vec2))
    mag1 = math.sqrt(sum(a * a for a in vec1))
    mag2 = math.sqrt(sum(b * b for b in vec2))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)