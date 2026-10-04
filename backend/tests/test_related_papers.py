import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.literature.related_paper_service import build_literature_queries, discover_related_papers, MAX_CANDIDATE_PAPERS, MAX_STORED_RELATED_PAPERS
from app.models.schema import RelatedPaper

@pytest.fixture
def mock_db_session():
    with patch("app.services.literature.related_paper_service.SessionLocal") as mock:
        yield mock

@pytest.fixture
def mock_search():
    with patch("app.services.literature.related_paper_service.search_academic_papers") as mock:
        yield mock

def test_build_literature_queries_and_placeholders():
    profile = MagicMock()
    profile.research_topic = "Deep Learning for Diabetic Retinopathy"
    profile.research_problem = "Not explicitly stated"
    profile.methodology = "N/A"
    profile.methods = ["Transfer Learning", "Unknown"]
    profile.algorithms = ["ResNet50"]
    profile.models = ["None"]
    profile.key_concepts = ["retinal fundus"]
    profile.research_domain = "Computer Science"
    profile.sub_domains = ["Not specified"]
    profile.application_domain = "Healthcare"
    profile.keywords = ["diabetic retinopathy"]

    queries = build_literature_queries(profile)
    assert len(queries) <= 5
    
    q_str = " ".join(queries).lower()
    
    assert "not explicitly stated" not in q_str
    assert "n/a" not in q_str
    assert "unknown" not in q_str
    assert "none" not in q_str
    assert "not specified" not in q_str
    
    # Assert real terms are present (case insensitive)
    queries_lower = [q.lower() for q in queries]
    assert "deep learning for diabetic retinopathy" in queries_lower
    assert "transfer learning" in queries_lower
    assert "resnet50 retinal fundus" in queries_lower
    assert "computer science healthcare diabetic retinopathy" in queries_lower

@pytest.mark.asyncio
async def test_missing_research_profile(mock_db_session):
    session_instance = mock_db_session.return_value
    mock_paper = MagicMock()
    session_instance.query.return_value.filter.return_value.first.side_effect = [mock_paper, None]
    
    result = await discover_related_papers(1)
    assert result == {"error": "Research profile must be generated before related paper discovery."}

@pytest.mark.asyncio
async def test_duplicate_removal(mock_db_session, mock_search):
    mock_paper = MagicMock()
    mock_paper.id = 1
    mock_paper.title = "Source"
    mock_paper.doi = "10/src"
    mock_paper.references = []
    
    mock_profile = MagicMock()
    mock_profile.research_topic = "Topic"
    
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.side_effect = [mock_paper, mock_profile]
    session_instance.query.return_value.filter.return_value.filter.return_value.first.return_value = None
    session_instance.query.return_value.filter.return_value.all.return_value = []
    
    mock_search.return_value = {
        "total": 3,
        "results": [
            {"title": "Paper A", "doi": "10/a"},
            {"title": "Paper A", "doi": "10/a"},
            {"title": "Paper A duplicate", "doi": "10/a"},
        ],
        "providers": {}
    }
    
    result = await discover_related_papers(1)
    assert result["candidates_found"] == 1

@pytest.mark.asyncio
async def test_uploaded_paper_exclusion(mock_db_session, mock_search):
    mock_paper = MagicMock()
    mock_paper.id = 1
    mock_paper.title = "Source Paper"
    mock_paper.doi = "10/src"
    mock_paper.references = []
    
    mock_profile = MagicMock()
    mock_profile.research_topic = "Topic"
    
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.side_effect = [mock_paper, mock_profile]
    session_instance.query.return_value.filter.return_value.filter.return_value.first.return_value = None
    session_instance.query.return_value.filter.return_value.all.return_value = []
    
    mock_search.return_value = {
        "total": 2,
        "results": [
            {"title": "Source Paper", "doi": "10/src"},
            {"title": "Other Paper", "doi": "10/other"}
        ],
        "providers": {}
    }
    
    result = await discover_related_papers(1)
    assert result["candidates_found"] == 1
    assert result["papers_stored"] == 1

@pytest.mark.asyncio
async def test_reference_detection(mock_db_session, mock_search):
    mock_paper = MagicMock()
    mock_paper.id = 1
    mock_paper.title = "Source"
    mock_paper.doi = "10/src"
    mock_paper.references = [MagicMock(title="Ref Paper", doi="10/ref")]
    
    mock_profile = MagicMock()
    mock_profile.research_topic = "Topic"
    
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.side_effect = [mock_paper, mock_profile]
    session_instance.query.return_value.filter.return_value.filter.return_value.first.return_value = None
    session_instance.query.return_value.filter.return_value.all.return_value = []
    
    mock_search.return_value = {
        "total": 2,
        "results": [
            {"title": "Ref Paper", "doi": "10/ref"},
            {"title": "New Paper", "doi": "10/new"}
        ],
        "providers": {}
    }
    
    await discover_related_papers(1)
    
    add_calls = session_instance.add.call_args_list
    papers = [c[0][0] for c in add_calls]
    
    ref_paper = next(p for p in papers if p.title == "Ref Paper")
    new_paper = next(p for p in papers if p.title == "New Paper")
    
    assert ref_paper.is_existing_reference is True
    assert new_paper.is_existing_reference is False

@pytest.mark.asyncio
async def test_candidate_and_storage_limits(mock_db_session, mock_search):
    mock_paper = MagicMock()
    mock_paper.id = 1
    mock_paper.title = "Source"
    mock_paper.doi = "10/src"
    mock_paper.references = []
    
    mock_profile = MagicMock()
    mock_profile.research_topic = "Topic"
    
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.side_effect = [mock_paper, mock_profile]
    session_instance.query.return_value.filter.return_value.filter.return_value.first.return_value = None
    session_instance.query.return_value.filter.return_value.all.return_value = []
    
    results = [{"title": f"Paper {i}", "doi": f"10/{i}"} for i in range(150)]
    mock_search.return_value = {
        "total": 150,
        "results": results,
        "providers": {}
    }
    
    result = await discover_related_papers(1)
    
    assert result["candidates_found"] <= MAX_CANDIDATE_PAPERS
    assert result["papers_stored"] <= MAX_STORED_RELATED_PAPERS
    assert session_instance.add.call_count <= MAX_STORED_RELATED_PAPERS

@pytest.mark.asyncio
async def test_database_duplicate_protection(mock_db_session, mock_search):
    mock_paper = MagicMock()
    mock_paper.id = 1
    mock_paper.title = "Source"
    mock_paper.doi = "10/src"
    mock_paper.references = []
    
    mock_profile = MagicMock()
    mock_profile.research_topic = "Topic"
    
    session_instance = mock_db_session.return_value
    mock_existing = RelatedPaper(id=99, title="Existing", doi="10/existing")
    session_instance.query.return_value.filter.return_value.first.side_effect = [mock_paper, mock_profile]
    session_instance.query.return_value.filter.return_value.filter.return_value.first.return_value = mock_existing
    
    mock_search.return_value = {
        "total": 1,
        "results": [{"title": "Existing", "doi": "10/existing"}],
        "providers": {}
    }
    
    result = await discover_related_papers(1)
    
    assert session_instance.add.call_count == 0
    assert result["papers_stored"] == 0

@pytest.mark.asyncio
async def test_provider_failure(mock_db_session):
    with patch("app.services.literature.related_paper_service.search_academic_papers") as mock_search_fail:
        mock_paper = MagicMock()
        mock_paper.id = 1
        mock_paper.title = "Source"
        mock_paper.doi = "10/src"
        mock_paper.references = []
        
        mock_profile = MagicMock()
        mock_profile.research_topic = "Topic"
        mock_profile.research_problem = "Problem"
        
        session_instance = mock_db_session.return_value
        session_instance.query.return_value.filter.return_value.first.side_effect = [mock_paper, mock_profile]
        session_instance.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        session_instance.query.return_value.filter.return_value.all.return_value = []
        
        async def mock_fail_succeed(query, limit):
            if "Topic" in query:
                raise Exception("Provider failed")
            return {"results": [{"title": "Success Paper", "doi": "10/success"}], "providers": {}}
            
        mock_search_fail.side_effect = mock_fail_succeed
        
        result = await discover_related_papers(1)
        assert result["status"] == "completed"
        assert result["candidates_found"] >= 1

@pytest.mark.asyncio
async def test_empty_results(mock_db_session, mock_search):
    mock_paper = MagicMock()
    mock_paper.id = 1
    mock_paper.title = "Source"
    mock_paper.doi = "10/src"
    mock_paper.references = []
    
    mock_profile = MagicMock()
    mock_profile.research_topic = "Topic"
    
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.side_effect = [mock_paper, mock_profile]
    session_instance.query.return_value.filter.return_value.filter.return_value.first.return_value = None
    session_instance.query.return_value.filter.return_value.all.return_value = []
    
    mock_search.return_value = {
        "total": 0,
        "results": [],
        "providers": {}
    }
    
    result = await discover_related_papers(1)
    assert result["status"] == "completed"
    assert result["candidates_found"] == 0
    assert result["papers_stored"] == 0
