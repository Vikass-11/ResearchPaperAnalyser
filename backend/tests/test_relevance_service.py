import pytest
from unittest.mock import patch, MagicMock
from app.services.literature.relevance_service import rank_related_papers, calculate_paper_relevance, build_profile_context
from app.models.schema import RelatedPaper, ResearchProfile
from datetime import datetime

@pytest.fixture
def mock_db_session():
    with patch("app.services.literature.relevance_service.SessionLocal") as mock:
        yield mock

def test_build_profile_context():
    profile = ResearchProfile(
        research_topic="deep learning medical imaging",
        research_problem="tumor detection",
        methodology="quantitative",
        methods=["cnn", "transfer learning"],
        algorithms=["resnet"],
        models=["unet"],
        key_concepts=["segmentation"],
        keywords=["mri", "brain"],
        research_domain="computer science",
        application_domain="healthcare",
        sub_domains=["computer vision"]
    )
    context = build_profile_context(profile)
    assert "deep" in context["topic"]
    assert "tumor" in context["problem"]
    assert "cnn" in context["method"]
    assert "resnet" in context["algorithm"]
    assert "unet" in context["algorithm"]
    assert "segmentation" in context["concept"]
    assert "mri" in context["keyword"]
    assert "healthcare" in context["domain"]

def test_exact_topic_match():
    # Test 1
    profile = ResearchProfile(research_topic="deep learning medical imaging", research_problem="tumor")
    context = build_profile_context(profile)
    paper = RelatedPaper(title="Deep learning for medical imaging", abstract="Tumor detection", year=2000)
    score, category, breakdown = calculate_paper_relevance(paper, context)
    assert breakdown["topic"] >= 50.0
    assert score > 15
    assert category in ["Directly Related", "Alternative Approach", "Other Related"]

def test_no_overlap():
    # Test 2
    profile = ResearchProfile(research_topic="deep learning medical imaging")
    context = build_profile_context(profile)
    paper = RelatedPaper(title="quantum physics", abstract="string theory", year=2000)
    score, category, breakdown = calculate_paper_relevance(paper, context)
    assert score == 0.0
    assert category == "Other Related"

def test_keyword_overlap():
    # Test 3
    profile = ResearchProfile(keywords=["mri", "segmentation", "brain"])
    context = build_profile_context(profile)
    paper = RelatedPaper(title="title", abstract="MRI segmentation of brain", year=2000)
    score, category, breakdown = calculate_paper_relevance(paper, context)
    assert breakdown["keyword"] >= 50.0
    assert score > 0

def test_methodological_similarity():
    # Test 4
    profile = ResearchProfile(research_problem="medical", methods=["cnn"], algorithms=["resnet"])
    context = build_profile_context(profile)
    paper = RelatedPaper(title="agriculture", abstract="cnn resnet", year=2000)
    score, category, breakdown = calculate_paper_relevance(paper, context)
    assert breakdown["method"] >= 30.0
    assert breakdown["algorithm"] >= 30.0
    assert category == "Methodologically Related"

def test_domain_similarity():
    # Test 5
    profile = ResearchProfile(research_domain="computer science", application_domain="healthcare")
    context = build_profile_context(profile)
    paper = RelatedPaper(title="IT in healthcare", abstract="computer science", year=2000)
    score, category, breakdown = calculate_paper_relevance(paper, context)
    assert breakdown["domain"] >= 50.0
    assert category == "Domain Related"

def test_alternative_approach():
    # Test 6
    profile = ResearchProfile(research_problem="temperature control", methods=["PID controller"])
    context = build_profile_context(profile)
    paper = RelatedPaper(title="temperature control", abstract="fuzzy logic", year=2000)
    score, category, breakdown = calculate_paper_relevance(paper, context)
    assert breakdown["problem"] >= 50.0
    assert breakdown["method"] == 0.0
    assert category == "Alternative Approach"

def test_recent_development():
    # Test 7
    profile = ResearchProfile(research_topic="LLM")
    context = build_profile_context(profile)
    paper = RelatedPaper(title="LLM advances", year=datetime.now().year - 1)
    score, category, breakdown = calculate_paper_relevance(paper, context)
    assert breakdown["recency"] >= 50.0
    assert category == "Recent Development"

def test_existing_reference_independence():
    # Test 8
    profile = ResearchProfile(research_topic="deep learning")
    context = build_profile_context(profile)
    paper1 = RelatedPaper(title="deep learning", is_existing_reference=True, year=2000)
    paper2 = RelatedPaper(title="deep learning", is_existing_reference=False, year=2000)
    
    score1, cat1, br1 = calculate_paper_relevance(paper1, context)
    score2, cat2, br2 = calculate_paper_relevance(paper2, context)
    
    assert score1 == score2

def test_score_bounds():
    # Test 9
    profile = ResearchProfile(research_topic="deep learning")
    context = build_profile_context(profile)
    paper = RelatedPaper(title="deep learning", year=datetime.now().year)
    score, _, _ = calculate_paper_relevance(paper, context)
    assert 0 <= score <= 100

def test_determinism():
    # Test 10
    profile = ResearchProfile(research_topic="deep learning")
    context = build_profile_context(profile)
    paper = RelatedPaper(title="deep learning", year=2020)
    score1, cat1, _ = calculate_paper_relevance(paper, context)
    score2, cat2, _ = calculate_paper_relevance(paper, context)
    assert score1 == score2
    assert cat1 == cat2

def test_missing_abstract():
    # Test 11
    profile = ResearchProfile(research_topic="deep learning")
    context = build_profile_context(profile)
    paper = RelatedPaper(title="deep learning", abstract=None, year=2020)
    score, cat, _ = calculate_paper_relevance(paper, context)
    assert score > 0

def test_missing_research_profile(mock_db_session):
    # Test 12
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.return_value = None
    
    result = rank_related_papers(1)
    assert "error" in result

def test_empty_related_paper_list(mock_db_session):
    # Test 13
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.return_value = ResearchProfile(paper_id=1)
    session_instance.query.return_value.filter.return_value.all.return_value = []
    
    result = rank_related_papers(1)
    assert result["papers_analyzed"] == 0

def test_database_persistence(mock_db_session):
    # Test 14
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.return_value = ResearchProfile(paper_id=1, research_topic="test")
    
    paper = RelatedPaper(id=1, title="test", year=2020)
    session_instance.query.return_value.filter.return_value.all.return_value = [paper]
    
    result = rank_related_papers(1)
    
    assert session_instance.commit.called
    assert result["papers_analyzed"] == 1
    assert paper.relevance_score is not None
    assert paper.relationship_type is not None
    assert paper.score_breakdown is not None
