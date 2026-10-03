from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.schema import Paper, ResearchProfile, RelatedPaper, LiteratureAnalysis, LiteratureSurvey
from app.services.literature.research_profile_service import generate_research_profile
from app.services.literature.related_paper_service import discover_related_papers
from app.services.literature.relevance_service import rank_related_papers
from app.services.literature.literature_analysis_service import analyze_related_papers
from app.services.literature.literature_survey_service import generate_literature_survey
from app.schemas.literature_analysis import LiteratureAnalysisResponse
from app.schemas.literature_survey import LiteratureSurveyResponse

router = APIRouter()

@router.get("/{paper_id}/literature/research-profile")
def get_research_profile(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail={"error": {"code": "PAPER_NOT_FOUND", "message": "Paper not found."}})
        
    profile = db.query(ResearchProfile).filter(ResearchProfile.paper_id == paper_id).first()
    
    if not profile:
        return {"paper_id": paper_id, "message": "Research profile is pending or not generated yet.", "research_profile": None}
        
    return {
        "paper_id": paper_id,
        "research_profile": {
            "research_domain": profile.research_domain,
            "sub_domains": profile.sub_domains,
            "research_topic": profile.research_topic,
            "research_problem": profile.research_problem,
            "research_objective": profile.research_objective,
            "methodology": profile.methodology,
            "methods": profile.methods,
            "algorithms": profile.algorithms,
            "models": profile.models,
            "technologies": profile.technologies,
            "datasets": profile.datasets,
            "key_concepts": profile.key_concepts,
            "keywords": profile.keywords,
            "research_questions": profile.research_questions,
            "application_domain": profile.application_domain
        }
    }

@router.post("/{paper_id}/literature/research-profile/generate")
async def manual_generate_profile(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail={"error": {"code": "PAPER_NOT_FOUND", "message": "Paper not found."}})
        
    profile = await generate_research_profile(paper_id)
    if not profile:
        raise HTTPException(status_code=500, detail="Failed to generate research profile")
        
    return {"message": "Research profile generated successfully", "research_profile": profile.model_dump()}

@router.get("/{paper_id}/literature/related")
def get_related_papers(paper_id: int, page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    if limit > 100:
        raise HTTPException(status_code=400, detail={"error": {"code": "VALIDATION_ERROR", "message": "Limit cannot exceed 100."}})
    if page < 1:
        raise HTTPException(status_code=400, detail={"error": {"code": "VALIDATION_ERROR", "message": "Page must be >= 1."}})
        
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail={"error": {"code": "PAPER_NOT_FOUND", "message": "Paper not found."}})
        
    offset = (page - 1) * limit
    
    query = db.query(RelatedPaper).filter(RelatedPaper.source_paper_id == paper_id)
    total = query.count()
    
    papers = query.order_by(RelatedPaper.citation_count.desc().nullslast()).offset(offset).limit(limit).all()
    
    return {
        "paper_id": paper_id,
        "total": total,
        "page": page,
        "limit": limit,
        "papers": [
            {
                "id": p.id,
                "title": p.title,
                "authors": p.authors,
                "year": p.year,
                "doi": p.doi,
                "url": p.url,
                "venue": p.venue,
                "citation_count": p.citation_count,
                "source": p.source,
                "is_existing_reference": p.is_existing_reference,
                "category": p.category
            } for p in papers
        ]
    }

@router.post("/{paper_id}/literature/related/discover")
async def manual_discover_related_papers(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail={"error": {"code": "PAPER_NOT_FOUND", "message": "Paper not found."}})
        
    result = await discover_related_papers(paper_id)
    if "error" in result:
        raise HTTPException(status_code=500, detail={"error": {"code": "INTERNAL_ERROR", "message": result["error"]}})
        
    return {"message": "Discovery completed successfully", "stats": result}

@router.get("/{paper_id}/literature/ranked")
def get_ranked_papers(paper_id: int, page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    if limit > 100:
        raise HTTPException(status_code=400, detail={"error": {"code": "VALIDATION_ERROR", "message": "Limit cannot exceed 100."}})
    if page < 1:
        raise HTTPException(status_code=400, detail={"error": {"code": "VALIDATION_ERROR", "message": "Page must be >= 1."}})
        
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail={"error": {"code": "PAPER_NOT_FOUND", "message": "Paper not found."}})
        
    offset = (page - 1) * limit
    
    query = db.query(RelatedPaper).filter(RelatedPaper.source_paper_id == paper_id).filter(RelatedPaper.relevance_score.isnot(None))
    total = query.count()
    
    # Order by relevance_score DESC
    papers = query.order_by(RelatedPaper.relevance_score.desc()).offset(offset).limit(limit).all()
    
    return {
        "paper_id": paper_id,
        "total": total,
        "page": page,
        "limit": limit,
        "papers": [
            {
                "id": p.id,
                "title": p.title,
                "authors": p.authors,
                "year": p.year,
                "doi": p.doi,
                "url": p.url,
                "venue": p.venue,
                "citation_count": p.citation_count,
                "source": p.source,
                "is_existing_reference": p.is_existing_reference,
                "category": p.category,
                "relationship_type": p.relationship_type,
                "relevance_score": p.relevance_score,
                "score_breakdown": p.score_breakdown
            } for p in papers
        ]
    }

@router.post("/{paper_id}/literature/rank")
def manual_rank_related_papers(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail={"error": {"code": "PAPER_NOT_FOUND", "message": "Paper not found."}})
        
    result = rank_related_papers(paper_id)
    if "error" in result:
        raise HTTPException(status_code=500, detail={"error": {"code": "INTERNAL_ERROR", "message": result["error"]}})
        
    return {"message": "Ranking completed successfully", "stats": result}

@router.get("/{paper_id}/literature/analysis", response_model=list[LiteratureAnalysisResponse])
def get_literature_analysis(paper_id: int, db: Session = Depends(get_db)):
    analyses = (
        db.query(LiteratureAnalysis)
        .join(RelatedPaper, LiteratureAnalysis.related_paper_id == RelatedPaper.id)
        .filter(RelatedPaper.source_paper_id == paper_id)
        .all()
    )
    if not analyses:
        raise HTTPException(status_code=404, detail={"error": {"code": "LITERATURE_ANALYSIS_NOT_FOUND", "message": "Literature analysis not found."}})
    return analyses

@router.post("/{paper_id}/literature/analyze")
async def analyze_literature(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail={"error": {"code": "PAPER_NOT_FOUND", "message": "Paper not found."}})
        
    result = await analyze_related_papers(paper_id)
    if "error" in result:
        raise HTTPException(status_code=500, detail={"error": {"code": "INTERNAL_ERROR", "message": result["error"]}})
    return {"message": "Literature analysis completed successfully", "stats": result}

@router.get("/{paper_id}/literature/survey", response_model=LiteratureSurveyResponse)
def get_literature_survey(paper_id: int, db: Session = Depends(get_db)):
    survey = db.query(LiteratureSurvey).filter(LiteratureSurvey.paper_id == paper_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail={"error": {"code": "LITERATURE_SURVEY_NOT_FOUND", "message": "Literature survey not found."}})
    return survey

@router.post("/{paper_id}/literature/survey/generate")
async def generate_survey(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail={"error": {"code": "PAPER_NOT_FOUND", "message": "Paper not found."}})
        
    result = await generate_literature_survey(paper_id)
    if "error" in result:
        raise HTTPException(status_code=500, detail={"error": {"code": "INTERNAL_ERROR", "message": result["error"]}})
    return {"message": "Literature survey generated successfully", "stats": result}

from app.models.schema import ResearchGap
from app.schemas.research_gap import ResearchGapSchema
from app.services.literature.research_gap_service import detect_research_gaps

@router.get("/{paper_id}/literature/gaps")
def get_research_gaps(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail={"error": {"code": "PAPER_NOT_FOUND", "message": "Paper not found."}})
        
    gaps = db.query(ResearchGap).filter(ResearchGap.paper_id == paper_id).order_by(ResearchGap.confidence.desc()).all()
    
    return {
        "paper_id": paper_id,
        "gaps": [
            {
                "gap_type": g.gap_type,
                "title": g.title,
                "description": g.description,
                "evidence": g.evidence,
                "significance": g.significance,
                "related_paper_ids": g.related_paper_ids,
                "confidence": g.confidence,
                "proposed_direction": g.proposed_direction
            } for g in gaps
        ]
    }

@router.post("/{paper_id}/literature/gaps/detect")
async def manual_detect_research_gaps(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail={"error": {"code": "PAPER_NOT_FOUND", "message": "Paper not found."}})
        
    result = await detect_research_gaps(paper_id)
    if "error" in result:
        status_code = 400 if "must be completed" in result["error"] or "must be generated" in result["error"] else 500
        raise HTTPException(status_code=status_code, detail={"error": {"code": "PROCESSING_FAILED", "message": result["error"]}})
    return result

from app.models.schema import RecentResearch
from app.services.literature.recent_research_service import detect_recent_research

@router.get("/{paper_id}/literature/recent")
def get_recent_research(paper_id: int, page: int = 1, limit: int = 20, db: Session = Depends(get_db)):
    if limit > 100:
        raise HTTPException(status_code=400, detail={"error": {"code": "VALIDATION_ERROR", "message": "Limit cannot exceed 100."}})
    if page < 1:
        raise HTTPException(status_code=400, detail={"error": {"code": "VALIDATION_ERROR", "message": "Page must be >= 1."}})
        
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail={"error": {"code": "PAPER_NOT_FOUND", "message": "Paper not found."}})
        
    offset = (page - 1) * limit
    query = db.query(RecentResearch).filter(RecentResearch.paper_id == paper_id)
    total = query.count()
    recent = query.order_by(RecentResearch.relevance_score.desc()).offset(offset).limit(limit).all()
    
    return {
        "paper_id": paper_id,
        "page": page,
        "limit": limit,
        "total": total,
        "recent_research": [
            {
                "id": r.id,
                "external_id": r.external_id,
                "source": r.source,
                "title": r.title,
                "authors": r.authors,
                "abstract": r.abstract,
                "year": r.year,
                "doi": r.doi,
                "url": r.url,
                "venue": r.venue,
                "citation_count": r.citation_count,
                "relevance_score": r.relevance_score,
                "relevance_reason": r.relevance_reason,
                "relationship_type": r.relationship_type,
                "is_newer_than_target": r.is_newer_than_target,
                "addresses_gap": r.addresses_gap,
                "related_gap_ids": r.related_gap_ids
            } for r in recent
        ]
    }

@router.post("/{paper_id}/literature/recent/discover")
async def manual_discover_recent_research(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail={"error": {"code": "PAPER_NOT_FOUND", "message": "Paper not found."}})
        
    result = await detect_recent_research(paper_id)
    if "error" in result:
        status_code = 400 if "must be generated" in result["error"] else 500
        raise HTTPException(status_code=status_code, detail={"error": {"code": "PROCESSING_FAILED", "message": result["error"]}})
        
    return result



from fastapi.responses import Response
from app.services.research_report_service import build_research_report, generate_markdown_report, generate_pdf_report
from app.schemas.research_report import ResearchReportSchema

@router.get("/{paper_id}/export/json", response_model=ResearchReportSchema, tags=["Export"])
def export_report_json(paper_id: int, db: Session = Depends(get_db)):
    try:
        report = build_research_report(paper_id, db)
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"error": {"code": "PAPER_NOT_FOUND", "message": str(e)}})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": {"code": "EXPORT_FAILED", "message": str(e)}})

@router.get("/{paper_id}/export/markdown", tags=["Export"])
def export_report_markdown(paper_id: int, db: Session = Depends(get_db)):
    try:
        report = build_research_report(paper_id, db)
        md_content = generate_markdown_report(report)
        return Response(
            content=md_content,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=scholargraph_report_{paper_id}.md"}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"error": {"code": "PAPER_NOT_FOUND", "message": str(e)}})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": {"code": "EXPORT_FAILED", "message": str(e)}})

@router.get("/{paper_id}/export/pdf", tags=["Export"])
def export_report_pdf(paper_id: int, db: Session = Depends(get_db)):
    try:
        report = build_research_report(paper_id, db)
        pdf_bytes = generate_pdf_report(report)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=scholargraph_report_{paper_id}.pdf"}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"error": {"code": "PAPER_NOT_FOUND", "message": str(e)}})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": {"code": "EXPORT_FAILED", "message": str(e)}})
