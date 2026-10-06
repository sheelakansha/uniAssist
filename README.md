# uniAssist

An evidence-first university assistant for NSUT. It combines deterministic SQLite tools for student records with version-aware institutional-document retrieval. The system never lets an LLM invent student facts, policies, calculations, citations, or eligibility decisions.

## Features

- React + Vite academic-assistant dashboard
- FastAPI API with OpenAPI documentation
- Deterministic tools for students, attendance, results, backlogs, and courses
- Chroma-backed institutional knowledge base with source authority and document-version metadata
- SHA-256/canonical-content version checks and active/superseded documents
- Evidence, citations, request IDs, and privacy-minimised audit records
- Local Ollama explanation layer; no student information is sent to cloud LLMs

## Architecture

`React → FastAPI → router → SQLite tools / Chroma policy retrieval → deterministic decision → evidence, citations, audit`

## Quick start

Prerequisites: Python 3.11+, Node 20+, Docker Desktop (for Chroma), and optionally Ollama.

```powershell
git clone https://github.com/sheelakansha/uniAssist.git
cd uniAssist
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Start Chroma:

```powershell
docker compose up chroma -d
```

Run FastAPI:

```powershell
$env:CHROMA_HOST='localhost'
$env:CHROMA_PORT='8001'
python -m uvicorn app.api.main:app --reload --port 8000
```

Run React in another terminal:

```powershell
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

Open the dashboard at the Vite URL (normally `http://localhost:5173`) and API documentation at `http://localhost:8000/docs`.

## Real document ingestion

PDFs are intentionally excluded from Git. Place approved official documents beneath `real_corpus/`, register them, then ingest:

```powershell
python scripts/register_source.py --id nsut-regulations --file real_corpus/regulations.pdf --title "NSUT B.Tech Regulations" --category regulations --authority 100
python scripts/ingest.py
```

Use `python scripts/ingest.py --metadata-only` for a fast source-registration pass while embeddings are prepared. Run the normal ingestion command afterward to create BGE vectors.

## Development

```powershell
pytest -q
python scripts/validate_data.py
python scripts/evaluate.py
```

Generated state (`runtime/`, `chroma-data/`, local PDFs, caches, and virtual environments) is excluded from Git. Copy `.env.example` to `.env` and configure local services as needed.
