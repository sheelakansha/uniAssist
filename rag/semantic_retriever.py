import os
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer
from app.config import settings

class SemanticUniversityRetriever:
    def __init__(
        self,
        chroma_path="runtime/chroma",
        model_name="BAAI/bge-small-en-v1.5"
    ):
        # Docker/server mode is the default when CHROMA_HOST is configured.
        # PersistentClient remains available for an offline local-only setup.
        host = os.getenv("CHROMA_HOST", settings.chroma_host)
        self.client = (chromadb.HttpClient(host=host, port=int(os.getenv("CHROMA_PORT", "8001")))
                       if host else chromadb.PersistentClient(path=str(Path(chroma_path))))
        self.collection = self.client.get_or_create_collection(
            "nsut_knowledge",
            metadata={"hnsw:space": "cosine"}
        )
        self.model = SentenceTransformer(model_name)

    def search(self, query: str, top_k: int = 5):
        embedding = self.model.encode(
            [query],
            normalize_embeddings=True,
            show_progress_bar=False
        ).tolist()

        result = self.collection.query(
            query_embeddings=embedding,
            n_results=top_k,
            where={"status": "active"}
        )

        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        sources = []
        for i, doc in enumerate(documents):
            meta = metadatas[i] if i < len(metadatas) else {}
            distance = distances[i] if i < len(distances) else None
            sources.append({
                "text": doc,
                "document_id": meta.get("document_id"),
                "source_id": meta.get("source_id"),
                "category": meta.get("category"),
                "version_label": meta.get("version_label"),
                "effective_from": meta.get("effective_from"),
                "title": meta.get("title"),
                "source_uri": meta.get("source_uri"),
                "authority_level": meta.get("authority_level"),
                "distance": distance
            })

        return {
            "query": query,
            "count": len(sources),
            "sources": sources
        }
