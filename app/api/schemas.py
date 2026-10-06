from typing import Any
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    query: str = Field(min_length=2, max_length=2000)
    student_id: str | None = Field(default=None, pattern=r"^[Ss]\d{4}$")
class ChatResponse(BaseModel):
    request_id: str; answer: str; intent: str; decision: dict[str, Any] | None = None
    evidence: dict[str, Any] = {}; sources: list[dict[str, Any]] = []; citations: list[dict[str, Any]] = []; audit: dict[str, Any] = {}
