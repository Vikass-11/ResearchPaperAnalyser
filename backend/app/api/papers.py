from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
import shutil
import os
import asyncio

from app.models.database import get_db
from app.models.schema import Paper, Section
from app.schemas.paper import PaperResponse, PaperDetailResponse, PaperUploadResponse
from app.services.grobid_service import process_pdf_with_grobid
from app.services.pdf_service import extract_text_from_pdf
from app.services.llm_provider import analyze_paper_sections

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def process_paper_background(paper_id: int, file_path: str, db: Session):
    """Background task to process the uploaded PDF using GROBID and LLM."""
    try:
        # Update status
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            return
        
        paper.processing_status = "PARSING"
        db.commit()
        
        # 1. Process with GROBID
        sections_text = ""
        try:
            grobid_data = await process_pdf_with_grobid(file_path)
            
            # Update Metadata
            paper.title = grobid_data["metadata"]["title"] or paper.title
            paper.authors = grobid_data["metadata"]["authors"]
            paper.abstract = grobid_data["metadata"]["abstract"]
            paper.year = grobid_data["metadata"]["year"]
            
            # Save Sections
            for sec in grobid_data["sections"]:
                db_sec = Section(
                    paper_id=paper.id,
                    section_name=sec["section_name"],
                    content=sec["content"]
                )
                db.add(db_sec)
                sections_text += f"\n\n### {sec['section_name']} ###\n{sec['content']}"
                
            db.commit()
        except Exception as e:
            print(f"GROBID failed, falling back to PyMuPDF: {e}")
            raw_text = extract_text_from_pdf(file_path)
            sections_text = f"### Full Text ###\n{raw_text}"
            
            # Create a single fallback section
            db_sec = Section(
                paper_id=paper.id,
                section_name="Full Text (Fallback Extraction)",
                content=raw_text
            )
            db.add(db_sec)
            db.commit()

        # 2. Analyze with LLM
        if sections_text:
            paper.processing_status = "ANALYZING"
            db.commit()
            
            analysis = await analyze_paper_sections(sections_text)
            
            paper.summary = analysis.summary
            paper.problem_statement = analysis.problem_statement
            paper.objective = analysis.objective
            paper.methodology = analysis.methodology
            paper.dataset = analysis.dataset
            paper.results = analysis.results
            paper.contributions = analysis.contributions
            paper.limitations = analysis.limitations
            paper.future_work = analysis.future_work

        paper.processing_status = "COMPLETED"
        db.commit()
    except Exception as e:
        # Re-fetch just in case of stale session
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if paper:
            paper.processing_status = "ERROR"
            paper.error_message = str(e)
            db.commit()

# Need to run async background task properly
def run_process_paper_background(paper_id: int, file_path: str, db: Session):
    asyncio.run(process_paper_background(paper_id, file_path, db))

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
        
    db_paper = Paper(
        title=file.filename,
        file_path=file_path,
        processing_status="UPLOADED"
    )
    db.add(db_paper)
    db.commit()
    db.refresh(db_paper)
    
    # Trigger background processing wrapper
    background_tasks.add_task(run_process_paper_background, db_paper.id, file_path, db)
    
    return {"id": db_paper.id, "status": "UPLOADED", "message": "Paper uploaded and processing started."}

@router.get("/", response_model=list[PaperResponse])
def get_papers(db: Session = Depends(get_db)):
    papers = db.query(Paper).all()
    return papers

@router.get("/{paper_id}", response_model=PaperDetailResponse)
def get_paper(paper_id: int, db: Session = Depends(get_db)):
    # Need to load sections for detailed view
    paper = db.query(Paper).options(joinedload(Paper.sections)).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper
