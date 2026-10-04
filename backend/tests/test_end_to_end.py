import pytest
import asyncio
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.models.schema import Base, Paper, ResearchProfile, RelatedPaper, LiteratureAnalysis, LiteratureSurvey, ResearchGap, RecentResearch
from app.services.literature.research_profile_service import generate_research_profile
from app.services.literature.related_paper_service import discover_related_papers
from app.services.literature.relevance_service import rank_related_papers
from app.services.literature.literature_analysis_service import analyze_related_papers
from app.services.literature.literature_survey_service import generate_literature_survey
from app.services.literature.research_gap_service import detect_research_gaps
from app.services.literature.recent_research_service import detect_recent_research
from app.services.research_report_service import build_research_report, generate_markdown_report, generate_pdf_report

# Setup test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine_test = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine_test)
    Base.metadata.create_all(bind=engine_test)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def mock_session_local():
    with patch('app.services.literature.research_profile_service.SessionLocal', TestingSessionLocal), \
         patch('app.services.literature.related_paper_service.SessionLocal', TestingSessionLocal), \
         patch('app.services.literature.relevance_service.SessionLocal', TestingSessionLocal), \
         patch('app.services.literature.literature_analysis_service.SessionLocal', TestingSessionLocal), \
         patch('app.services.literature.literature_survey_service.SessionLocal', TestingSessionLocal), \
         patch('app.services.literature.research_gap_service.SessionLocal', TestingSessionLocal), \
         patch('app.services.literature.recent_research_service.SessionLocal', TestingSessionLocal), \
         patch('app.services.research_report_service.SessionLocal', TestingSessionLocal):
        yield

@pytest.mark.asyncio
async def test_complete_e2e_lifecycle(db_session):
    # 1. Create test paper
    paper = Paper(
        title="Attention Is All You Need",
        abstract="The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...",
        authors=["Ashish Vaswani", "Noam Shazeer"],
        year=2017,
        file_path="mock.pdf",
        processing_status="completed"
    )
    db_session.add(paper)
    db_session.commit()
    
    paper_id = paper.id
    
    # 2. Verify paper exists
    assert db_session.query(Paper).count() == 1
    
    # 3. Generate ResearchProfile
    result_profile = await generate_research_profile(paper_id)
    if not result_profile or (isinstance(result_profile, dict) and "error" in result_profile):
        pytest.skip("Ollama/LLM unavailable for Research Profile")
        
    profile = db_session.query(ResearchProfile).filter_by(paper_id=paper_id).first()
    assert profile is not None
    assert profile.research_domain is not None
    
    # 4. Discover RelatedPapers
    result_related = await discover_related_papers(paper_id)
    if "error" in result_related:
        pytest.skip(f"Academic APIs unavailable: {result_related['error']}")
    
    related_count = db_session.query(RelatedPaper).filter_by(source_paper_id=paper_id).count()
    assert related_count > 0
    
    # 5. Rank RelatedPapers
    result_rank = rank_related_papers(paper_id)
    assert "error" not in result_rank
    
    ranked_paper = db_session.query(RelatedPaper).filter_by(source_paper_id=paper_id).filter(RelatedPaper.relevance_score.isnot(None)).first()
    assert ranked_paper is not None
    
    # 6. Generate LiteratureAnalysis
    result_analysis = await analyze_related_papers(paper_id)
    if "error" in result_analysis:
        pytest.skip(f"LLM unavailable for Literature Analysis: {result_analysis['error']}")
        
    analysis_count = db_session.query(LiteratureAnalysis).count()
    assert analysis_count > 0
    
    # 7. Generate LiteratureSurvey
    result_survey = await generate_literature_survey(paper_id)
    if "error" in result_survey:
        pytest.skip(f"LLM unavailable for Literature Survey: {result_survey['error']}")
        
    survey = db_session.query(LiteratureSurvey).filter_by(paper_id=paper_id).first()
    assert survey is not None
    
    # 8. Detect ResearchGaps
    result_gaps = await detect_research_gaps(paper_id)
    if "error" in result_gaps:
        pytest.skip(f"LLM unavailable for Research Gaps: {result_gaps['error']}")
        
    gaps_count = db_session.query(ResearchGap).filter_by(paper_id=paper_id).count()
    assert gaps_count > 0
    
    # 9. Discover RecentResearch
    result_recent = await detect_recent_research(paper_id)
    if "error" in result_recent:
        pytest.skip(f"Academic APIs unavailable for Recent Research: {result_recent['error']}")
        
    recent_count = db_session.query(RecentResearch).filter_by(paper_id=paper_id).count()
    assert recent_count > 0
    
    # 10. Build ResearchReport
    report = build_research_report(paper_id, db_session)
    assert report.paper.title == "Attention Is All You Need"
    assert report.research_profile.available
    assert report.literature.available
    assert report.literature_survey.available
    assert report.research_gaps.available
    assert report.recent_research.available
    
    # 11. Generate Markdown and PDF
    md = generate_markdown_report(report)
    assert "Attention Is All You Need" in md
    
    pdf = generate_pdf_report(report)
    assert len(pdf) > 0
    assert pdf.startswith(b"%PDF")
