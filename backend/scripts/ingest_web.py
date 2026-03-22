import uuid
import wikipedia

from backend.routes.upload_routes import chunk_text
from backend.database.chroma_client import collection


topics = [
    "Artificial intelligence",
    "Machine learning",
    "Deep learning",
    "Computer vision",
    "Natural language processing",
    "Reinforcement learning",
]


def ingest_web():

    for topic in topics:

        print("Fetching:", topic)

        try:
            text = wikipedia.page(topic).content
        except Exception as e:
            print("Skipping:", topic, e)
            continue

        chunks = chunk_text(text)

        document_id = str(uuid.uuid4())

        ids = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):

            ids.append(str(uuid.uuid4()))
            documents.append(chunk)

            metadatas.append({
                "document_id": document_id,
                "source": topic,
                "chunk": i,
                "type": "wikipedia"
            })

        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        print("Stored", len(chunks), "chunks from", topic)


if __name__ == "__main__":
    ingest_web()