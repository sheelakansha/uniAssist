"""Chroma indexing for explicitly registered, verified institutional documents."""
from __future__ import annotations
from hashlib import sha256
from app.config import settings

def chunk_text(text: str, size: int = 1200, overlap: int = 200) -> list[str]:
    text=" ".join(text.split())
    if not text: return []
    chunks=[]; start=0
    while start < len(text):
        end=min(len(text),start+size)
        if end < len(text):
            boundary=text.rfind(". ",start,end)
            if boundary > start + size//2: end=boundary+1
        chunks.append(text[start:end]); start=max(end-overlap,start+1)
    return chunks

class ChromaIndexer:
    def __init__(self):
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError("Install chromadb-client and sentence-transformers before ingesting real documents.") from exc
        self.client=chromadb.HttpClient(host=settings.chroma_host,port=settings.chroma_port)
        self.collection=self.client.get_or_create_collection("nsut_knowledge",metadata={"hnsw:space":"cosine"})
        self.model=SentenceTransformer("BAAI/bge-small-en-v1.5")
    def index(self, document_id: str, text: str, metadata: dict) -> list[tuple[int,str,str]]:
        chunks=chunk_text(text)
        if not chunks: raise ValueError("Document has no extractable text")
        ids=[f"{document_id}:{i}" for i in range(len(chunks))]
        vectors=self.model.encode(chunks,normalize_embeddings=True,show_progress_bar=False).tolist()
        metas=[metadata | {"document_id":document_id,"chunk_index":i,"status":"active"} for i in range(len(chunks))]
        self.collection.add(ids=ids,documents=chunks,embeddings=vectors,metadatas=metas)
        return [(i,sha256(chunk.encode()).hexdigest(),ids[i]) for i,chunk in enumerate(chunks)]
    def delete_document(self, document_id: str) -> None:
        self.collection.delete(where={"document_id":document_id})
