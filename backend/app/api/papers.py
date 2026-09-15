from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import shutil
import os

from app.models.database import get_db
from app.models.schema import Paper
from app.schemas.paper import PaperResponse, PaperUploadResponse
from app.services.pdf_service import extract_text_from_pdf

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def process_paper_background(paper_id: int, file_path: str, db: Session):
    """Background task to process the uploaded PDF."""
    try:
        # Update status
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            return
        
        paper.processing_status = "PARSING"
        db.commit()
        
        # Extract text (Phase 1 basic extraction)
        text = extract_text_from_pdf(file_path)
        
        # (Later phases will include GROBID, LLM processing, etc.)
        
        paper.processing_status = "COMPLETED"
        paper.summary = f"Extracted {len(text)} characters of text."
        db.commit()
    except Exception as e:
        paper.processing_status = "ERROR"
        paper.error_message = str(e)
        db.commit()

@router.post("/upload", response_model=PaperUploadResponse)
def upload_paper(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Create DB entry
    db_paper = Paper(
        title=file.filename,
        file_path=file_path,
        processing_status="UPLOADED"
    )
    db.add(db_paper)
    db.commit()
    db.refresh(db_paper)
    
    # Trigger background processing
    background_tasks.add_task(process_paper_background, db_paper.id, file_path, db)
    
    return {"id": db_paper.id, "status": "UPLOADED", "message": "Paper uploaded and processing started."}

@router.get("/", response_model=list[PaperResponse])
def get_papers(db: Session = Depends(get_db)):
    papers = db.query(Paper).all()
    return papers

@router.get("/{paper_id}")
def get_paper(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper
