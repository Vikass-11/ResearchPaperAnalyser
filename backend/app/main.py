from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import papers
from app.models.database import init_db

# Initialize database
init_db()

app = FastAPI(
    title="Research Paper Analyzer API",
    description="AI-Powered Research Paper Analysis & Citation Intelligence System",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(papers.router, prefix="/api/v1/papers", tags=["papers"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
