import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

client = chromadb.Client(
    Settings(
        persist_directory="./chroma_storage"
    )
)

embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = client.get_or_create_collection(
    name="documents",
    embedding_function=embedding_function
)