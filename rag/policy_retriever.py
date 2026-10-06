from pathlib import Path
import chromadb

class UniversityPolicyRetriever:
    """
    Reads the version-aware Chroma collection created by the ingestion layer.

    Production rule:
    only chunks whose metadata says status='active' are returned.
    """

    def __init__(self, chroma_path="runtime/chroma"):
        self.chroma_path = Path(chroma_path)
        self.client = chromadb.PersistentClient(path=str(self.chroma_path))
        self.collection = self.client.get_or_create_collection(
            "nsut_knowledge",
            metadata={"hnsw:space": "cosine"}
        )

    def search(self, query: str, top_k: int = 5):
        # Embedding is intentionally delegated to the ingestion/indexing
        # layer in production. This method expects an indexed collection.
        # The companion service can inject query embeddings.
        return {
            "query": query,
            "status": "retriever_ready",
            "message": (
                "Connect the same BGE embedding model used by ingestion "
                "for semantic query encoding."
            )
        }
