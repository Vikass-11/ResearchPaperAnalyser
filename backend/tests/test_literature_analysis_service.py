import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.literature.literature_analysis_service import analyze_related_papers, analyze_single_paper
from app.models.schema import RelatedPaper, ResearchProfile, LiteratureAnalysis
from app.schemas.literature_analysis import LiteratureAnalysisSchema
from app.services.literature.research_profile_service import normalize_list_field

@pytest.fixture
def mock_db_session():
    with patch("app.services.literature.literature_analysis_service.SessionLocal") as mock:
        yield mock

def test_missing_research_profile(mock_db_session):
    # Test 3
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.return_value = None
    
    result = asyncio.run(analyze_related_papers(1))
    assert "error" in result

def test_top_n_selection(mock_db_session):
    # Test 1 & 2
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.return_value = ResearchProfile(paper_id=1)
    
    # Mock related papers query
    query_mock = session_instance.query.return_value
    query_mock = query_mock.filter.return_value
    query_mock = query_mock.filter.return_value
    query_mock = query_mock.filter.return_value
    query_mock = query_mock.order_by.return_value
    query_mock.limit.return_value.all.return_value = [
        RelatedPaper(id=i, title=f"Paper {i}", relevance_score=100-i) for i in range(1, 11)
    ]
    
    with patch("app.services.literature.literature_analysis_service.analyze_single_paper") as mock_analyze:
        mock_analyze.return_value = {"status": "success", "related_paper_id": 1, "data": {}}
        result = asyncio.run(analyze_related_papers(1))
        
        assert result["papers_selected"] == 10
        assert mock_analyze.call_count == 10
        
        # Verify highest relevance scored paper is selected first
        first_call_args = mock_analyze.call_args_list[0]
        assert first_call_args[0][1] == 1 # ID is 1, which had highest score (99)

def test_list_normalization():
    # Test 7
    assert normalize_list_field("[]") == []
    assert normalize_list_field('["A", "B"]') == ["A", "B"]
    assert normalize_list_field(["A", "B"]) == ["A", "B"]
    assert normalize_list_field(None) == []
    assert normalize_list_field("") == []

@pytest.mark.asyncio
async def test_missing_abstract(mock_db_session):
    # Test 4
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.return_value = ResearchProfile(paper_id=1)
    
    paper_without_abstract = RelatedPaper(id=1, title="No Abstract Paper", abstract=None, relevance_score=50.0)
    
    query_mock = session_instance.query.return_value
    query_mock = query_mock.filter.return_value
    query_mock = query_mock.filter.return_value
    query_mock = query_mock.filter.return_value
    query_mock = query_mock.order_by.return_value
    query_mock.limit.return_value.all.return_value = [paper_without_abstract]
    
    with patch("app.services.llm_provider.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        mock_response.choices[0].message.tool_calls[0].function.arguments = '{"problem_statement": "Not available from retrieved metadata.", "objective": "Obj", "methodology": "Meth", "experimental_setup": "Exp", "research_direction": "Dir", "relevance_to_target": "Rel"}'
        mock_create.return_value = mock_response
        
        result = await analyze_related_papers(1)
        assert result["papers_analyzed"] == 1

@pytest.mark.asyncio
async def test_structured_output_validation():
    # Test 5
    with patch("app.services.llm_provider.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        mock_response.choices[0].message.tool_calls[0].function.arguments = '{"problem_statement": "Prob", "objective": "Obj", "methodology": "Meth", "experimental_setup": "Exp", "research_direction": "Dir", "relevance_to_target": "Rel", "methods": "[\\"CNN\\"]"}'
        mock_create.return_value = mock_response
        
        res = await analyze_single_paper(1, 1, {}, {})
        assert res["status"] == "success"
        assert res["data"]["problem_statement"] == "Prob"
        assert res["data"]["methods"] == ["CNN"]

@pytest.mark.asyncio
async def test_malformed_llm_response():
    # Test 6
    with patch("app.services.llm_provider.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        mock_response.choices[0].message.tool_calls[0].function.arguments = "invalid json"
        mock_create.return_value = mock_response
        
        res = await analyze_single_paper(1, 1, {}, {})
        assert res["status"] == "failed"

@pytest.mark.asyncio
async def test_llm_failure_isolation(mock_db_session):
    # Test 8
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.return_value = ResearchProfile(paper_id=1)
    
    papers = [
        RelatedPaper(id=1, title="Paper 1", relevance_score=50.0),
        RelatedPaper(id=2, title="Paper 2", relevance_score=40.0)
    ]
    
    query_mock = session_instance.query.return_value
    query_mock = query_mock.filter.return_value
    query_mock = query_mock.filter.return_value
    query_mock = query_mock.filter.return_value
    query_mock = query_mock.order_by.return_value
    query_mock.limit.return_value.all.return_value = papers
    
    # Mock analyze_single_paper to fail on first, succeed on second
    async def side_effect(paper_id, cand_id, t_ctx, c_ctx):
        if cand_id == 1:
            return {"status": "failed", "related_paper_id": cand_id, "error": "Fail"}
        return {"status": "success", "related_paper_id": cand_id, "data": {"problem_statement": "Prob"}}
        
    with patch("app.services.literature.literature_analysis_service.analyze_single_paper", side_effect=side_effect):
        result = await analyze_related_papers(1)
        assert result["papers_selected"] == 2
        assert result["papers_analyzed"] == 1
        assert result["papers_failed"] == 1

@pytest.mark.asyncio
async def test_idempotency_and_persistence(mock_db_session):
    # Test 9 and 11
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.return_value = ResearchProfile(paper_id=1)
    
    papers = [RelatedPaper(id=1, title="Paper 1", relevance_score=50.0)]
    
    query_mock = session_instance.query.return_value
    query_mock = query_mock.filter.return_value
    query_mock = query_mock.filter.return_value
    query_mock = query_mock.filter.return_value
    query_mock = query_mock.order_by.return_value
    query_mock.limit.return_value.all.return_value = papers
    
    existing_analysis = LiteratureAnalysis(id=1, related_paper_id=1, problem_statement="Old Prob")
    session_instance.query.return_value.filter.return_value.first.side_effect = [
        ResearchProfile(paper_id=1), # For profile query
        existing_analysis # For LiteratureAnalysis check
    ]
    
    with patch("app.services.literature.literature_analysis_service.analyze_single_paper") as mock_analyze:
        mock_analyze.return_value = {"status": "success", "related_paper_id": 1, "data": {"problem_statement": "New Prob"}}
        result = await analyze_related_papers(1)
        
        assert result["papers_analyzed"] == 1
        assert session_instance.add.call_count == 0 # Since it existed, it should update
        assert existing_analysis.problem_statement == "New Prob" # Updated field

@pytest.mark.asyncio
async def test_no_hallucinated_fallback():
    # Test 12
    with patch("app.services.llm_provider.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        mock_response.choices[0].message.tool_calls[0].function.arguments = '{"problem_statement": "Not available from retrieved metadata.", "objective": "Not available from retrieved metadata.", "methodology": "Not available from retrieved metadata.", "experimental_setup": "Not available from retrieved metadata.", "research_direction": "Not available from retrieved metadata.", "relevance_to_target": "Not available from retrieved metadata."}'
        mock_create.return_value = mock_response
        
        res = await analyze_single_paper(1, 1, {}, {})
        assert res["status"] == "success"
        assert res["data"]["problem_statement"] == "Not available from retrieved metadata."
        assert res["data"]["methodology"] == "Not available from retrieved metadata."

@pytest.mark.asyncio
async def test_concurrency_limit(mock_db_session):
    # Test 10
    from app.services.literature.literature_analysis_service import semaphore
    assert semaphore._value == 2
