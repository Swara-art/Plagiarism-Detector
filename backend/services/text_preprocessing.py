import re
import unicodedata

def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def preprocess_for_embedding(text: str) -> str:
    text = normalize_text(text)
    text = re.sub(r'http\S+|www\.\S+', '', text)
    text = re.sub(r'[^\w\s\.\,\!\?\;\:]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def split_into_sentences(text: str) -> list:
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 20]

def chunk_with_metadata(text: str, chunk_size: int = 500, overlap: int = 100):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append({"text": text[start:end], "start": start, "end": end})
        start += chunk_size - overlap
    return chunks