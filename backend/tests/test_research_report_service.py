import pytest
from app.services.research_report_service import build_research_report, generate_markdown_report, generate_pdf_report
from app.schemas.research_report import ResearchReportSchema
from app.models.schema import Paper, ResearchProfile, RelatedPaper, LiteratureAnalysis, LiteratureSurvey, ResearchGap, RecentResearch
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.models.schema import Base

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
def test_missing_paper(db_session):
    with pytest.raises(ValueError, match="Paper not found"):
        build_research_report(999, db_session)

def test_empty_pipeline(db_session):
    p = Paper(id=1, title="Test", file_path="test.pdf")
    db_session.add(p)
    db_session.commit()
    
    report = build_research_report(1, db_session)
    assert report.paper.title == "Test"
    assert not report.research_profile.available
    assert not report.literature.available
    assert not report.literature_survey.available
    assert not report.research_gaps.available
    assert not report.recent_research.available
    
    # Render should still work
    md = generate_markdown_report(report)
    assert "Test" in md
    
    pdf = generate_pdf_report(report)
    assert len(pdf) > 0

def test_full_pipeline(db_session):
    p = Paper(id=1, title="Full Paper", file_path="test.pdf", year=2026, authors=["Test Author"])
    db_session.add(p)
    
    rp = ResearchProfile(paper_id=1, research_domain="Test Domain")
    db_session.add(rp)
    
    related1 = RelatedPaper(id=1, source_paper_id=1, title="Rel1", relevance_score=0.9, citation_count=10)
    db_session.add(related1)
    
    db_session.flush()
    analysis = LiteratureAnalysis(related_paper_id=1, problem_statement="Test Prob")
    db_session.add(analysis)
    
    survey = LiteratureSurvey(paper_id=1, research_context="Context", research_landscape="Landscape", methodological_comparison="Comp", findings_synthesis="Synth", overall_synthesis="Over")
    db_session.add(survey)
    
    gap = ResearchGap(paper_id=1, title="Gap 1", confidence=0.8, gap_type="Methodological", description="A missing method")
    db_session.add(gap)
    
    recent = RecentResearch(paper_id=1, title="Rec1", year=2026, relevance_score=0.8, relationship_type="Extension")
    db_session.add(recent)
    
    db_session.commit()
    
    # Test JSON/Schema build
    report = build_research_report(1, db_session)
    assert report.paper.title == "Full Paper"
    assert report.research_profile.available
    assert report.literature.available
    assert len(report.literature.related_papers) == 1
    assert len(report.literature.analyses) == 1
    assert report.literature_survey.available
    assert report.research_gaps.available
    assert len(report.research_gaps.gaps) == 1
    assert report.recent_research.available
    assert len(report.recent_research.recent) == 1
    
    # Export Limits
    assert report.metadata.export_limits.related_papers_truncated == False
    
    # Test Markdown
    md = generate_markdown_report(report)
    assert "Full Paper" in md
    assert "Rel1" in md
    assert "Gap 1" in md
    assert "Rec1" in md
    
    # Test PDF
    pdf = generate_pdf_report(report)
    assert len(pdf) > 0
    assert pdf.startswith(b"%PDF")
