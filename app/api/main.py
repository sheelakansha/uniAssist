from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.schemas import ChatRequest, ChatResponse
from app.service import service
from tools.student import get_student
from tools.attendance import get_attendance
from tools.results import get_results
from tools.backlog import get_backlogs

app=FastAPI(title="NSUT AI Assistant", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://127.0.0.1:5173", "http://127.0.0.1:5174", "http://127.0.0.1:5175"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
@app.exception_handler(Exception)
async def safe_error(_, exc):
    # Details remain in server logs; clients receive no traceback or paths.
    return JSONResponse(status_code=500, content={"detail":"The request could not be completed safely."})
@app.get('/health')
def health():
    # Keep readiness independent of SQLite/Chroma latency. Detailed source
    # state remains available through the protected source endpoints.
    return {"status":"ok","service":"nsut-ai-assistant"}
@app.post('/chat',response_model=ChatResponse)
def chat(request: ChatRequest): return service.chat(request.query,request.student_id)
@app.get('/sources')
def sources(): return service.registry.sources()
@app.get('/documents/active')
def active_documents(): return service.registry.documents(active_only=True)
@app.post('/ingest/sync-all')
def sync_all(): return service.ingestion.sync_all()
@app.post('/ingest/sync/{source_id}')
def sync(source_id: str):
    try: return service.ingestion.sync(source_id)
    except ValueError as exc: raise HTTPException(404,str(exc))
@app.get('/student/{student_id}')
def student(student_id: str):
    result=get_student(student_id.upper())
    if not result.get('found'): raise HTTPException(404,f"Student {student_id.upper()} was not found.")
    return result
@app.get('/attendance/{student_id}')
def attendance(student_id: str): return get_attendance(student_id.upper())
@app.get('/results/{student_id}')
def results(student_id: str): return get_results(student_id.upper())
@app.get('/backlogs/{student_id}')
def backlogs(student_id: str): return get_backlogs(student_id.upper())
