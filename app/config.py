from dataclasses import dataclass
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]

@dataclass(frozen=True)
class Settings:
    sqlite_path: Path = ROOT / "database" / "university.db"
    registry_path: Path = ROOT / "runtime" / "registry.db"
    chroma_path: Path = ROOT / "runtime" / "chroma"
    chroma_host: str = os.getenv("CHROMA_HOST", "localhost")
    chroma_port: int = int(os.getenv("CHROMA_PORT", "8001"))
    # Deliberately empty until an administrator registers verified documents.
    corpus_path: Path = ROOT / "real_corpus"
    llm_mode: str = os.getenv("LLM_MODE", "mock").lower()
    llm_model: str = os.getenv("LOCAL_LLM_MODEL", "qwen2.5:7b-instruct")
    llm_base_url: str = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434/v1")
    top_k: int = int(os.getenv("RETRIEVAL_TOP_K", "6"))

settings = Settings()
