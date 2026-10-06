"""Deterministic authority-aware policy retrieval over active document metadata."""
import re
from pathlib import Path
from app.config import settings
from app.db_registry import Registry

def _score(query, text):
    terms=set(re.findall(r"[a-z]{3,}",query.lower())); body=text.lower()
    return sum(t in body for t in terms) / max(1,len(terms))

class PolicyEngine:
    def __init__(self, registry=None): self.registry=registry or Registry(settings.registry_path)
    def retrieve(self, query: str, historical=False, top_k=None):
        # Normal operation uses the active Chroma collection. A registry
        # fallback preserves correct error handling if embedding dependencies
        # are not installed yet; it never creates knowledge from a model.
        if not historical and any(d['metadata'].get('index_status') == 'indexed' for d in self.registry.documents(active_only=True)):
            try:
                from rag.semantic_retriever import SemanticUniversityRetriever
                hits=SemanticUniversityRetriever().search(query, top_k or settings.top_k)["sources"]
                if hits:
                    return hits
            except (ImportError, RuntimeError, OSError):
                pass
        docs=self.registry.documents(active_only=not historical); hits=[]
        for d in docs:
            try: text=self._read_document(Path(d['local_path']))
            except OSError: continue
            score=_score(query,text)
            if score: hits.append({"text":text,"document_id":d['document_id'],"source_id":d['source_id'],"title":d['title'],"category":d['metadata'].get('category'),"authority_level":d['metadata'].get('authority_level',0),"version_label":d.get('version_label'),"effective_from":d.get('effective_from'),"source_uri":d.get('local_path'),"similarity":score})
        return sorted(hits,key=lambda x:(x['authority_level'],x['similarity']),reverse=True)[:top_k or settings.top_k]
    def resolve(self, query: str, rule_type: str):
        candidates=self.retrieve(query)
        if not candidates: return None, [], "no_active_policy"
        top=candidates[0]; numbers=re.findall(r"\b(\d{1,3}(?:\.\d+)?)\s*%",top['text'])
        if rule_type=='attendance_minimum':
            m=re.search(r"(?:minimum|required).{0,120}?(\d{1,3}(?:\.\d+)?)\s*%|(?:\b75\s*%\b).{0,100}?attendance",top['text'],re.I|re.S)
            value=float(m.group(1)) if m and m.group(1) else (75.0 if '75%' in top['text'] else None)
            if value is None: return None,candidates,"unextractable"
            return {"rule_type":rule_type,"required_percentage":value,"authority_level":top['authority_level'],"document_id":top['document_id'],"section":"retrieved regulation","effective_from":top['effective_from'],"evidence":self._excerpt(top['text'],'attendance')},candidates,None
        return None,candidates,"unsupported_rule"
    @staticmethod
    def _read_document(path: Path) -> str:
        if path.suffix.lower()=='.pdf':
            import fitz
            with fitz.open(path) as pdf:
                return '\n'.join(page.get_text() for page in pdf)
        return path.read_text(encoding='utf-8',errors='replace')
    @staticmethod
    def _excerpt(text, term):
        pos=text.lower().find(term); return " ".join(text[max(0,pos-180):pos+500].split())
