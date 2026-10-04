import os
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api import papers, literature
from app.models.database import init_db
from app.config import CORS_ORIGINS_LIST, LLM_BASE_URL

# Initialize database
init_db()

app = FastAPI(
    title="Research Paper Analyzer API",
    description="AI-Powered Research Paper Analysis & Citation Intelligence System",
    version="1.0.0"
)

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    # Preserve {"error": ...} format without "detail" wrapper if the detail is already a dict with "error"
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    # Default fallback
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": "API_ERROR", "message": str(exc.detail)}})

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Prevent traceback leakage in production
    return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred."}})


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

app.include_router(papers.router, prefix="/api/v1/papers", tags=["Papers"])
app.include_router(literature.router, prefix="/api/v1/papers", tags=["Literature"])

@app.get("/api/v1/health", tags=["System"])
async def health_check():
    llm_status = "unavailable"
    try:
        if LLM_BASE_URL:
            # lightweight check, base_url is typically http://localhost:11434/v1, so we check root
            root_url = LLM_BASE_URL.replace("/v1", "/")
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(root_url)
                if res.status_code == 200:
                    llm_status = "available"
    except Exception:
        pass
    
    return {
        "status": "ok" if llm_status == "available" else "degraded",
        "database": "ok",
        "llm": llm_status
    }
