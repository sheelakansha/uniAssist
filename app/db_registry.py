"""Immutable policy-document registry and privacy-conscious request audit log."""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (source_id TEXT PRIMARY KEY, name TEXT NOT NULL,
 source_type TEXT NOT NULL, source_uri TEXT NOT NULL, category TEXT NOT NULL,
 authority_level INTEGER NOT NULL, enabled INTEGER NOT NULL DEFAULT 1,
 poll_minutes INTEGER NOT NULL DEFAULT 1440);
CREATE TABLE IF NOT EXISTS documents (document_id TEXT PRIMARY KEY, source_id TEXT NOT NULL,
 title TEXT NOT NULL, content_hash TEXT NOT NULL, canonical_hash TEXT NOT NULL,
 version_label TEXT, effective_from TEXT, effective_to TEXT, published_at TEXT,
 fetched_at TEXT NOT NULL, status TEXT NOT NULL, supersedes_document_id TEXT,
 local_path TEXT, metadata_json TEXT NOT NULL DEFAULT '{}', UNIQUE(source_id, content_hash));
CREATE INDEX IF NOT EXISTS idx_documents_active ON documents(status, source_id);
CREATE TABLE IF NOT EXISTS document_chunks (chunk_id TEXT PRIMARY KEY, document_id TEXT NOT NULL,
 chunk_index INTEGER NOT NULL, text_hash TEXT NOT NULL, chroma_id TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS audit_log (request_id TEXT PRIMARY KEY, timestamp TEXT NOT NULL,
 intent TEXT, tools_json TEXT NOT NULL, documents_json TEXT NOT NULL, decision_json TEXT,
 model TEXT, latency_ms INTEGER NOT NULL, llm_status TEXT NOT NULL);
"""
def now() -> str: return datetime.now(timezone.utc).isoformat()
class Registry:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True); self.path = path
        with self.connect() as conn: conn.executescript(SCHEMA)
    def connect(self):
        c = sqlite3.connect(self.path); c.row_factory = sqlite3.Row; return c
    def seed_source(self, s: dict[str, Any]) -> None:
        with self.connect() as c: c.execute("INSERT INTO sources VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(source_id) DO UPDATE SET name=excluded.name,source_type=excluded.source_type,source_uri=excluded.source_uri,category=excluded.category,authority_level=excluded.authority_level,enabled=excluded.enabled,poll_minutes=excluded.poll_minutes", (s['source_id'],s['name'],s['source_type'],s['source_uri'],s['category'],s['authority_level'],int(s.get('enabled',True)),s.get('poll_minutes',1440)))
    def sources(self) -> list[dict]:
        with self.connect() as c: return [dict(x) for x in c.execute("SELECT * FROM sources ORDER BY source_id")]
    def documents(self, active_only=False) -> list[dict]:
        q="SELECT * FROM documents"+(" WHERE status='active'" if active_only else "")+" ORDER BY fetched_at DESC"
        with self.connect() as c: return [self._doc(dict(x)) for x in c.execute(q)]
    def active_for_source(self, source_id: str):
        with self.connect() as c:
            r=c.execute("SELECT * FROM documents WHERE source_id=? AND status='active' ORDER BY fetched_at DESC LIMIT 1",(source_id,)).fetchone()
            return self._doc(dict(r)) if r else None
    def by_hash(self, source_id: str, content_hash: str):
        with self.connect() as c:
            r=c.execute("SELECT * FROM documents WHERE source_id=? AND content_hash=?",(source_id,content_hash)).fetchone()
            return self._doc(dict(r)) if r else None
    def add_document(self, d: dict) -> None:
        with self.connect() as c: c.execute("INSERT INTO documents VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (d['document_id'],d['source_id'],d['title'],d['content_hash'],d['canonical_hash'],d.get('version_label'),d.get('effective_from'),d.get('effective_to'),d.get('published_at'),d['fetched_at'],d['status'],d.get('supersedes_document_id'),d.get('local_path'),json.dumps(d.get('metadata',{}))))
    def supersede(self, document_id: str) -> None:
        with self.connect() as c: c.execute("UPDATE documents SET status='superseded' WHERE document_id=?",(document_id,))
    def add_chunks(self, document_id: str, chunks: list[tuple[int, str, str]]) -> None:
        with self.connect() as c:
            c.executemany("INSERT INTO document_chunks VALUES(?,?,?,?,?)", [(f"{document_id}:{i}",document_id,i,text_hash,chroma_id) for i,text_hash,chroma_id in chunks])
    def set_index_status(self, document_id: str, status: str) -> None:
        with self.connect() as c:
            row=c.execute("SELECT metadata_json FROM documents WHERE document_id=?",(document_id,)).fetchone()
            if row:
                metadata=json.loads(row["metadata_json"] or "{}")
                metadata["index_status"]=status
                c.execute("UPDATE documents SET metadata_json=? WHERE document_id=?",(json.dumps(metadata),document_id))
    def record_audit(self, r: dict) -> None:
        with self.connect() as c: c.execute("INSERT INTO audit_log VALUES(?,?,?,?,?,?,?,?,?)", (r['request_id'],now(),r.get('intent'),json.dumps(r.get('tools_used',[])),json.dumps(r.get('documents_retrieved',[])),json.dumps(r.get('decision')),r.get('model'),r['latency_ms'],r['llm_status']))
    @staticmethod
    def _doc(d: dict) -> dict: d['metadata']=json.loads(d.pop('metadata_json') or '{}'); return d
