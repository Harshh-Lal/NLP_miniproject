"""FastAPI backend application for CodeReviewer.NLP."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Ensure src is on python path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from code_reviewer.auditor import audit_commit

app = FastAPI(
    title="CodeReviewer.NLP API",
    description="Semantic Commit and PR Consistency Auditor API",
    version="0.1.0",
)

# Enable CORS for local Vite dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AuditRequest(BaseModel):
    message: str = Field(..., description="Commit message to audit", json_schema_extra={"example": "fixed login issue"})
    diff: str = Field(..., description="Unified git diff text", json_schema_extra={"example": "diff --git a/auth/session.py..."})


class HealthResponse(BaseModel):
    status: str
    version: str


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return health status."""
    return HealthResponse(status="ok", version="0.1.0")


@app.post("/audit")
def audit_endpoint(payload: AuditRequest) -> dict[str, Any]:
    """Execute consistency audit on provided message and git diff."""
    if not payload.message or not payload.message.strip():
        raise HTTPException(status_code=400, detail="Commit message cannot be empty.")
    try:
        report = audit_commit(payload.message, payload.diff)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit execution error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
