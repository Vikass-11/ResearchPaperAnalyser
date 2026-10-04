import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.literature.recent_research_service import detect_recent_research, calculate_recent_relevance, build_queries
from app.models.schema import Paper, ResearchProfile, ResearchGap, RelatedPaper, RecentResearch

@pytest.fixture
def mock_db_session():
    with patch("app.services.literature.recent_research_service.SessionLocal") as mock:
        yield mock
        
def setup_mock_db(session_instance):
    paper = Paper(id=1, title="Target Paper", year=2023)
    profile = ResearchProfile(paper_id=1, research_topic="AI", keywords=["ML", "DL"])
    gaps = [ResearchGap(id=1, title="Gap 1", gap_type="Dataset Gap")]
    related = [RelatedPaper(id=1, title="Related 1", doi="10.1234/related")]
    
    # sequence: paper, profile, gaps, related
    session_instance.query.return_value.filter.return_value.first.side_effect = [paper, profile]
    session_instance.query.return_value.filter.return_value.all.side_effect = [gaps, related]
    return paper, profile, gaps, related

@pytest.mark.asyncio
async def test_missing_research_profile(mock_db_session):
    session_instance = mock_db_session.return_value
    paper = Paper(id=1)
    session_instance.query.return_value.filter.return_value.first.side_effect = [paper, None]
    
    result = await detect_recent_research(1)
    assert "error" in result
    assert "Research profile must be generated" in result["error"]

@pytest.mark.asyncio
async def test_query_generation():
    profile = ResearchProfile(
        research_topic="Test Topic", 
        keywords=["k1", "k2"],
        research_problem="Problem",
        methodology="Meth",
        methods=["m1"],
        algorithms=["a1"],
        models=["m1"],
        research_domain="Domain"
    )
    gaps = [ResearchGap(title="Gap Title", gap_type="Type")]
    
    queries = build_queries(profile, gaps)
    assert len(queries) <= 5
    assert "Test Topic k1 k2" in queries
    assert "Gap Title Type" in queries

@pytest.mark.asyncio
@patch("app.services.literature.recent_research_service.search_academic_papers")
async def test_date_filtering_and_duplicates(mock_search_papers, mock_db_session):
    session_instance = mock_db_session.return_value
    setup_mock_db(session_instance)
    
    current_year = 2026
    
    mock_search_papers.return_value = {
        "results": [
            {"title": "Valid New", "year": 2025, "doi": "10.1/new"}, # Valid
            {"title": "Missing Year", "doi": "10.1/miss"}, # Excluded
            {"title": "Old Paper", "year": 2000, "doi": "10.1/old"}, # Excluded
            {"title": "Future Paper", "year": 2027, "doi": "10.1/fut"}, # Excluded
            {"title": "Target Paper", "year": 2024, "doi": "10.1234/target"}, # Excluded (target)
            {"title": "Related 1", "year": 2024, "doi": "10.1234/related"}, # Excluded (existing related)
            {"title": "Valid New", "year": 2025, "doi": "10.1/new"}, # Excluded (duplicate within batch)
        ]
    }
    
    with patch("app.services.literature.recent_research_service.datetime") as mock_datetime:
        mock_datetime.now.return_value.year = current_year
        result = await detect_recent_research(1)
        
        assert result["generated"] is True
        assert len(result["recent_research"]) == 1
        assert result["recent_research"][0]["title"] == "Valid New"

def test_relevance_and_recency_scoring():
    profile = ResearchProfile(
        research_topic="Machine Learning",
        research_problem="Optimization",
        keywords=["gradient", "descent"],
        algorithms=["sgd"]
    )
    gaps = [ResearchGap(id=1, title="Convergence speed", description="Needs faster convergence")]
    
    candidate = {
        "title": "Fast SGD for Machine Learning",
        "abstract": "We optimize gradient descent convergence speed.",
        "year": 2025
    }
    
    current_year = 2026
    
    score, rel_type, rel_reason, matched_gaps = calculate_recent_relevance(candidate, profile, gaps, current_year)
    
    assert score > 0.0
    assert 1 in matched_gaps
    assert rel_type == "Addresses Research Gap"

@pytest.mark.asyncio
@patch("app.services.literature.recent_research_service.search_academic_papers")
async def test_idempotency(mock_search_papers, mock_db_session):
    session_instance = mock_db_session.return_value
    setup_mock_db(session_instance)
    
    mock_search_papers.return_value = {
        "results": [
            {"title": "Valid New", "year": 2025, "doi": "10.1/new"}
        ]
    }
    
    result = await detect_recent_research(1)
    assert result["generated"] is True
    assert session_instance.query.return_value.filter.return_value.delete.call_count == 1

@pytest.mark.asyncio
@patch("app.services.literature.recent_research_service.search_academic_papers")
async def test_provider_failure_isolation(mock_search_papers, mock_db_session):
    session_instance = mock_db_session.return_value
    setup_mock_db(session_instance)
    
    mock_search_papers.side_effect = Exception("API limit")
    
    # Should not crash, just return empty list
    result = await detect_recent_research(1)
    assert result["generated"] is True
    assert len(result["recent_research"]) == 0

@pytest.mark.asyncio
@patch("app.services.literature.recent_research_service.search_academic_papers")
async def test_malformed_metadata_handling(mock_search_papers, mock_db_session):
    session_instance = mock_db_session.return_value
    setup_mock_db(session_instance)
    
    mock_search_papers.return_value = {
        "results": [
            {"title": None, "year": "invalid_year"} # Should be skipped
        ]
    }
    
    result = await detect_recent_research(1)
    assert result["generated"] is True
    assert len(result["recent_research"]) == 0

@pytest.mark.asyncio
@patch("app.services.literature.recent_research_service.search_academic_papers")
async def test_empty_academic_results(mock_search_papers, mock_db_session):
    session_instance = mock_db_session.return_value
    setup_mock_db(session_instance)
    
    mock_search_papers.return_value = {"results": []}
    
    result = await detect_recent_research(1)
    assert result["generated"] is True
    assert len(result["recent_research"]) == 0
