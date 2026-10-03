from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
import shutil
import os
import asyncio

from app.models.database import get_db, SessionLocal
from app.models.schema import Paper, Section, Reference, Citation
from app.schemas.paper import PaperResponse, PaperDetailResponse, PaperUploadResponse
from app.services.grobid_service import process_pdf_with_grobid
from app.services.pdf_service import extract_text_from_pdf
from app.services.llm_provider import analyze_paper_sections, synthesize_web_impact
from app.services.web_search_service import search_web_for_paper

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
                
            # Save References
            ref_id_map = {} # Maps XML ID (e.g., 'b0') to DB ID
            for ref_data in grobid_data.get("references", []):
                db_ref = Reference(
                    paper_id=paper.id,
                    reference_number=ref_data["id"],
                    title=ref_data["title"],
                    authors=ref_data["authors"],
                    year=ref_data["year"],
                    journal_conference=ref_data["journal_conference"],
                    raw_text=ref_data["raw_text"]
                )
                db.add(db_ref)
                db.flush() # To get the db_ref.id
                ref_id_map[ref_data["id"]] = db_ref.id
                
            # Save Citations
            for cit_data in grobid_data.get("citations", []):
                target_ref_db_id = ref_id_map.get(cit_data["reference_id"])
                if target_ref_db_id:
                    db_cit = Citation(
                        paper_id=paper.id,
                        reference_id=target_ref_db_id,
                        context=cit_data["context"],
                        section_name=cit_data["section_name"]
                    )
                    db.add(db_cit)
                
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

            # Phase 4: Generate Research Profile
            try:
                from app.services.literature.research_profile_service import generate_research_profile
                # Save existing state so it's available for the query
                db.commit()
                await generate_research_profile(paper_id)
            except Exception as e:
                print(f"Research profile generation failed: {e}")
                
            # Phase 5: Related Paper Discovery
            try:
                from app.services.literature.related_paper_service import discover_related_papers
                await discover_related_papers(paper_id)
            except Exception as e:
                print(f"Related paper discovery failed: {e}")
                
            # Phase 6: Relevance Ranking + Classification
            try:
                from app.services.literature.relevance_service import rank_related_papers
                rank_related_papers(paper_id)
            except Exception as e:
                print(f"Relevance ranking failed: {e}")
                
            # Phase 7: Detailed Literature Analysis
            try:
                from app.services.literature.literature_analysis_service import analyze_related_papers
                await analyze_related_papers(paper_id)
            except Exception as e:
                print(f"Detailed literature analysis failed: {e}")

            # Phase 8: Literature Survey Synthesis
            try:
                from app.services.literature.literature_survey_service import generate_literature_survey
                await generate_literature_survey(paper_id)
            except Exception as e:
                print(f"Literature survey synthesis failed: {e}")

            # Phase 9: Research Gap Detection
            try:
                from app.services.literature.research_gap_service import detect_research_gaps
                await detect_research_gaps(paper_id)
            except Exception as e:
                print(f"Research gap detection failed: {e}")

            # Phase 10: Recent Research Detection
            try:
                from app.services.literature.recent_research_service import detect_recent_research
                await detect_recent_research(paper_id)
            except Exception as e:
                print(f"Recent research detection failed: {e}")

        # 3. Web Search & Impact Analysis
        if paper.title:
            try:
                search_results = await search_web_for_paper(paper.title, paper.authors)
                web_impact = await synthesize_web_impact(paper.title, search_results)
                paper.web_impact_analysis = web_impact
            except Exception as e:
                print(f"Web impact analysis failed: {e}")
                paper.web_impact_analysis = "Failed to generate web impact analysis."

        # 4. Search Web for top References
        try:
            # Query top 3 references from DB to avoid lazy load issues
            top_refs = db.query(Reference).filter(Reference.paper_id == paper_id).limit(3).all()
            for ref in top_refs:
                if ref.title and ref.title != "Unknown Title":
                    try:
                        ref_search = await search_web_for_paper(ref.title, ref.authors)
                        if ref_search:
                            ref_impact = await synthesize_web_impact(ref.title, ref_search)
                            ref.ai_summary = ref_impact
                            db.commit()
                    except Exception as e:
                        print(f"Failed web search for reference {ref.title}: {e}")
        except Exception as e:
            print(f"Reference processing failed: {e}")

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
def run_process_paper_background(paper_id: int, file_path: str):
    db = SessionLocal()
    try:
        asyncio.run(process_paper_background(paper_id, file_path, db))
    finally:
        db.close()

from app.config import MAX_UPLOAD_SIZE_BYTES
import uuid

@router.post("/upload", response_model=PaperUploadResponse)
async def upload_paper(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail={"error": {"code": "VALIDATION_ERROR", "message": "Only PDF files are allowed."}})
        
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail={"error": {"code": "VALIDATION_ERROR", "message": "Invalid MIME type. Must be application/pdf."}})

    # Check file size without reading entire file into memory at once if possible, 
    # but since it's SpooledTemporaryFile in FastAPI, we can read chunks
    file_size = 0
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}.pdf"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            while chunk := await file.read(8192):
                file_size += len(chunk)
                if file_size > MAX_UPLOAD_SIZE_BYTES:
                    buffer.close()
                    os.remove(file_path)
                    raise HTTPException(
                        status_code=413, 
                        detail={"error": {"code": "PAYLOAD_TOO_LARGE", "message": f"File exceeds maximum allowed size of {MAX_UPLOAD_SIZE_BYTES / (1024*1024):.0f} MB."}}
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail={"error": {"code": "UPLOAD_FAILED", "message": "Failed to save uploaded file."}})
        
    if file_size == 0:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail={"error": {"code": "VALIDATION_ERROR", "message": "File is empty."}})
        
    db_paper = Paper(
        title=file.filename,
        file_path=file_path,
        processing_status="UPLOADED"
    )
    db.add(db_paper)
    db.commit()
    db.refresh(db_paper)
    
    # Trigger background processing wrapper
    background_tasks.add_task(run_process_paper_background, db_paper.id, file_path)
    
    return {"id": db_paper.id, "status": "UPLOADED", "message": "Paper uploaded and processing started."}

@router.get("/", response_model=dict)
def get_papers(page: int = 1, limit: int = 20, db: Session = Depends(get_db)):
    if limit > 100:
        raise HTTPException(status_code=400, detail={"error": {"code": "VALIDATION_ERROR", "message": "Limit cannot exceed 100."}})
    if page < 1:
        raise HTTPException(status_code=400, detail={"error": {"code": "VALIDATION_ERROR", "message": "Page must be >= 1."}})
    
    total = db.query(Paper).count()
    offset = (page - 1) * limit
    papers = db.query(Paper).offset(offset).limit(limit).all()
    # Simple dict response for list endpoints
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "items": [
            {
                "id": p.id,
                "title": p.title,
                "year": p.year,
                "processing_status": p.processing_status
            } for p in papers
        ]
    }

@router.get("/{paper_id}", response_model=PaperDetailResponse)
def get_paper(paper_id: int, db: Session = Depends(get_db)):
    # Need to load sections for detailed view
    paper = db.query(Paper).options(
        joinedload(Paper.sections),
        joinedload(Paper.references).joinedload(Reference.citations)
    ).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail={"error": {"code": "PAPER_NOT_FOUND", "message": "Paper not found."}})
    return paper

from app.models.schema import ResearchProfile, RelatedPaper, LiteratureAnalysis, LiteratureSurvey, ResearchGap, RecentResearch

@router.get("/{paper_id}/pipeline/status")
def get_pipeline_status(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail={"error": {"code": "PAPER_NOT_FOUND", "message": "Paper not found."}})
        
    profile = db.query(ResearchProfile).filter(ResearchProfile.paper_id == paper_id).first()
    related_count = db.query(RelatedPaper).filter(RelatedPaper.source_paper_id == paper_id).count()
    
    # Actually, we can check LiteratureAnalysis presence via a related_paper
    analysis_count = db.query(LiteratureAnalysis).join(RelatedPaper).filter(RelatedPaper.source_paper_id == paper_id).count()
    
    survey = db.query(LiteratureSurvey).filter(LiteratureSurvey.paper_id == paper_id).first()
    gaps_count = db.query(ResearchGap).filter(ResearchGap.paper_id == paper_id).count()
    recent_count = db.query(RecentResearch).filter(RecentResearch.paper_id == paper_id).count()
    
    # We can infer states
    return {
        "paper_id": paper_id,
        "status": paper.processing_status.lower(),
        "stages": {
            "pdf_extraction": {
                "status": "completed" if paper.processing_status not in ["UPLOADED", "ERROR"] else ("failed" if paper.processing_status == "ERROR" else "pending")
            },
            "ai_analysis": {
                "status": "completed" if paper.processing_status == "COMPLETED" else ("failed" if paper.processing_status == "ERROR" else "pending")
            },
            "research_profile": {
                "status": "completed" if profile else "pending"
            },
            "related_papers": {
                "status": "completed" if related_count > 0 else "pending",
                "count": related_count
            },
            "ranking": {
                "status": "completed" if related_count > 0 else "pending"
            },
            "literature_analysis": {
                "status": "completed" if analysis_count > 0 else "pending",
                "count": analysis_count
            },
            "literature_survey": {
                "status": "completed" if survey else "pending"
            },
            "research_gaps": {
                "status": "completed" if gaps_count > 0 else "pending",
                "count": gaps_count
            },
            "recent_research": {
                "status": "completed" if recent_count > 0 else "pending",
                "count": recent_count
            }
        }
    }

@router.get("/{paper_id}/research-summary")
def get_research_summary(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail={"error": {"code": "PAPER_NOT_FOUND", "message": "Paper not found."}})
        
    profile = db.query(ResearchProfile).filter(ResearchProfile.paper_id == paper_id).first()
    related_count = db.query(RelatedPaper).filter(RelatedPaper.source_paper_id == paper_id).count()
    analysis_count = db.query(LiteratureAnalysis).join(RelatedPaper).filter(RelatedPaper.source_paper_id == paper_id).count()
    survey = db.query(LiteratureSurvey).filter(LiteratureSurvey.paper_id == paper_id).first()
    gaps_count = db.query(ResearchGap).filter(ResearchGap.paper_id == paper_id).count()
    recent_count = db.query(RecentResearch).filter(RecentResearch.paper_id == paper_id).count()
    
    return {
        "paper": {
            "id": paper.id,
            "title": paper.title,
            "year": paper.year,
            "authors": paper.authors
        },
        "pipeline": {
            "status": paper.processing_status.lower()
        },
        "research_profile": {
            "research_topic": profile.research_topic if profile else None,
            "research_problem": profile.research_problem if profile else None
        } if profile else None,
        "literature": {
            "related_count": related_count,
            "analyzed_count": analysis_count,
            "survey_available": survey is not None,
            "research_gap_count": gaps_count,
            "recent_research_count": recent_count
        }
    }

@router.delete("/{paper_id}")
def delete_paper(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail={"error": {"code": "PAPER_NOT_FOUND", "message": "Paper not found."}})
    
    try:
        # Related models that need explicit cascade due to relationships
        # We need to delete ResearchGaps, RecentResearch, LiteratureSurvey, ResearchProfile, RelatedPaper (and its analyses)
        
        # 1. RecentResearch
        db.query(RecentResearch).filter(RecentResearch.paper_id == paper_id).delete()
        
        # 2. ResearchGap
        db.query(ResearchGap).filter(ResearchGap.paper_id == paper_id).delete()
        
        # 3. LiteratureSurvey
        db.query(LiteratureSurvey).filter(LiteratureSurvey.paper_id == paper_id).delete()
        
        # 4. LiteratureAnalysis (via RelatedPaper)
        related_ids = [rp.id for rp in db.query(RelatedPaper.id).filter(RelatedPaper.source_paper_id == paper_id).all()]
        if related_ids:
            db.query(LiteratureAnalysis).filter(LiteratureAnalysis.related_paper_id.in_(related_ids)).delete(synchronize_session=False)
            
        # 5. RelatedPaper
        db.query(RelatedPaper).filter(RelatedPaper.source_paper_id == paper_id).delete()
        
        # 6. ResearchProfile
        db.query(ResearchProfile).filter(ResearchProfile.paper_id == paper_id).delete()
        
        # The core entities (Section, Reference, Citation) usually cascade or we can delete them
        db.query(Citation).filter(Citation.paper_id == paper_id).delete()
        db.query(Reference).filter(Reference.paper_id == paper_id).delete()
        db.query(Section).filter(Section.paper_id == paper_id).delete()
        
        # 7. Paper
        db.delete(paper)
        db.commit()
        
        # Cleanup file if exists
        if paper.file_path and os.path.exists(paper.file_path):
            try:
                os.remove(paper.file_path)
            except:
                pass
                
        return {"status": "success", "message": "Paper and all related data deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"error": {"code": "INTERNAL_ERROR", "message": str(e)}})

@router.get("/{paper_id}/graph")
def get_paper_graph(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).options(joinedload(Paper.references)).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail={"error": {"code": "PAPER_NOT_FOUND", "message": "Paper not found."}})
        
    nodes = []
    links = []
    
    # Add the main paper as the root node
    nodes.append({
        "id": f"paper_{paper.id}",
        "name": paper.title or "Uploaded Paper",
        "group": "main",
        "val": 20
    })
    
    # Add references as nodes and create links
    for ref in paper.references:
        ref_id = f"ref_{ref.id}"
        nodes.append({
            "id": ref_id,
            "name": ref.title or ref.raw_text[:50] + "...",
            "group": "reference",
            "val": 5
        })
        links.append({
            "source": f"paper_{paper.id}",
            "target": ref_id
        })
        
    return {"nodes": nodes, "links": links}
