import json, hashlib, re, uuid
from datetime import datetime, timezone
from pathlib import Path
from app.config import settings
from app.db_registry import Registry
from ingestion.indexer import ChromaIndexer

AUTHORITY = {"regulations": 100, "policy": 90, "academic_calendar": 80, "fees": 70, "curriculum": 60, "notice": 50}

def canonical(text: str) -> str: return re.sub(r"\s+", " ", text).strip()
def digest(value: bytes | str) -> str:
    if isinstance(value, str): value=value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()
def utcnow() -> str: return datetime.now(timezone.utc).isoformat()

class IngestionEngine:
    """Registers only bundled/admin-configured sources; never accepts user URLs."""
    def __init__(self, registry=None): self.registry=registry or Registry(settings.registry_path)
    def bootstrap_sources(self):
        """Load only explicit administrator-reviewed sources; never seed demos."""
        source_file=settings.registry_path.parent / 'sources.json'
        if not source_file.exists():
            return
        for source in json.loads(source_file.read_text(encoding='utf-8')):
            self.registry.seed_source(source)
    def sync_all(self, metadata_only: bool=False):
        self.bootstrap_sources(); return [self.sync(s["source_id"], metadata_only=metadata_only) for s in self.registry.sources() if s["enabled"]]
    def sync(self, source_id: str, metadata_only: bool=False):
        source=next((s for s in self.registry.sources() if s["source_id"]==source_id),None)
        if not source: raise ValueError("Unknown allowlisted source")
        path=Path(source["source_uri"]); raw=path.read_bytes(); text=self._extract_text(path)
        byte_hash, canonical_hash=digest(raw),digest(canonical(text))
        if old_exact:=self.registry.by_hash(source_id,byte_hash):
            if old_exact["metadata"].get("index_status") == "pending" and not metadata_only:
                chunks=ChromaIndexer().index(old_exact["document_id"],text,{"source_id":source_id,"title":source["name"],"category":source["category"],"authority_level":int(source["authority_level"]),"version_label":"registered","effective_from":"","source_uri":str(path)})
                self.registry.add_chunks(old_exact["document_id"],chunks); self.registry.set_index_status(old_exact["document_id"],"indexed")
                return {"status":"indexed_existing","document_id":old_exact["document_id"],"chunks_indexed":len(chunks)}
            return {"status":"unchanged","document_id":old_exact["document_id"]}
        active=self.registry.active_for_source(source_id)
        if active and active["canonical_hash"]==canonical_hash: return {"status":"unchanged_canonical","document_id":active["document_id"]}
        document_id=str(uuid.uuid4())
        chunks=[]; indexer=None
        if not metadata_only:
            indexer=ChromaIndexer()
            # Index first: a failed embedding/index operation must never hide
            # the previously active official document.
            chunks=indexer.index(document_id,text,{"source_id":source_id,"title":source["name"],"category":source["category"],"authority_level":int(source["authority_level"]),"version_label":"registered","effective_from":"","source_uri":str(path)})
        if active:
            if indexer: indexer.delete_document(active["document_id"])
            self.registry.supersede(active["document_id"])
        self.registry.add_document({"document_id":document_id,"source_id":source_id,"title":source["name"],"content_hash":byte_hash,"canonical_hash":canonical_hash,"version_label":"registered", "effective_from":None,"status":"active","fetched_at":utcnow(),"supersedes_document_id":active["document_id"] if active else None,"local_path":str(path),"metadata":{"category":source["category"],"authority_level":source["authority_level"],"index_status":"pending" if metadata_only else "indexed"}})
        if chunks: self.registry.add_chunks(document_id,chunks)
        return {"status":"registered_pending_index" if metadata_only else "updated","document_id":document_id,"superseded_document_id":active["document_id"] if active else None,"chunks_indexed":len(chunks)}
    @staticmethod
    def _extract_text(path: Path) -> str:
        if path.suffix.lower()=='.pdf':
            import fitz
            with fitz.open(path) as pdf: return '\n'.join(page.get_text() for page in pdf)
        return path.read_text(encoding='utf-8',errors='replace')
    def _text_for(self, doc_id):
        aliases={
            "NSUT-BTECH-REG-2019":"nsut_btech_regulations_2019_pdf.txt",
            "NSUT-ACADEMIC-CAL-2026-ODD":"nsut_academic_calendar_jul_dec_2026_pdf.txt",
            "NSUT-FEE-2023-24":"nsut_annual_fee_2023_24_pdf.txt",
            "NSUT-SYL-OS":"nsut_operating_systems_syllabus_pdf.txt",
            "NSUT-SYL-DIGITAL":"nsut_digital_circuits_systems_syllabus_pdf.txt",
            "NSUT-SYL-DATA-STRUCTURES":"nsut_data_structures_syllabus_pdf.txt",
            "NSUT-SYL-DBMS":"nsut_dbms_syllabus_pdf.txt",
            "NSUT-SYL-MPA":"nsut_microprocessor_architecture_syllabus_pdf.txt",
            "NSUT-SYL-SNS":"nsut_signals_and_systems_syllabus_pdf.txt",
        }
        if doc_id in aliases: return settings.corpus_path / aliases[doc_id]
        key=doc_id.lower().replace("-","_")
        candidates=list(settings.corpus_path.glob(f"{key.replace('nsut_','nsut_')}*.txt"))
        if not candidates:
            # registry names and extracted names differ only in a few human-readable cases
            tokens=[x for x in key.split("_") if x not in {"nsut","syl","btech"}]
            candidates=[p for p in settings.corpus_path.glob("*.txt") if all(t in p.name.lower() for t in tokens[:2])]
        if not candidates: raise FileNotFoundError(f"No extracted text for {doc_id}")
        return candidates[0]
    @staticmethod
    def _category(kind): return {"regulation":"regulations","fee_notification":"fees","syllabus":"curriculum"}.get(kind,kind)
