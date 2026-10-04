import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.literature.literature_survey_service import generate_literature_survey
from app.models.schema import RelatedPaper, ResearchProfile, LiteratureAnalysis, LiteratureSurvey
from app.schemas.literature_survey import LiteratureSurveySchema

@pytest.fixture
def mock_db_session():
    with patch("app.services.literature.literature_survey_service.SessionLocal") as mock:
        yield mock

def test_missing_research_profile(mock_db_session):
    # Test 1
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.return_value = None
    
    result = asyncio.run(generate_literature_survey(1))
    assert "error" in result
    assert "Research profile must be generated" in result["error"]

def test_missing_literature_analysis(mock_db_session):
    # Test 2
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.return_value = ResearchProfile(paper_id=1)
    
    # Mock literature analysis query
    query_mock = session_instance.query.return_value
    query_mock = query_mock.join.return_value
    query_mock = query_mock.filter.return_value
    query_mock = query_mock.order_by.return_value
    query_mock.limit.return_value.all.return_value = []
    
    result = asyncio.run(generate_literature_survey(1))
    assert "error" in result
    assert "Detailed literature analysis (Phase 7) must be completed" in result["error"]

def test_top_n_selection(mock_db_session):
    # Test 3 & 4 (Top N selection and Relevance Ordering)
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.return_value = ResearchProfile(paper_id=1)
    
    analyses = [LiteratureAnalysis(related_paper=RelatedPaper(id=i, title=f"Paper {i}", relevance_score=100-i)) for i in range(1, 11)]
    
    query_mock = session_instance.query.return_value
    query_mock = query_mock.join.return_value
    query_mock = query_mock.filter.return_value
    query_mock = query_mock.order_by.return_value
    query_mock.limit.return_value.all.return_value = analyses
    
    with patch("app.services.literature.literature_survey_service.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        
        mock_response.choices[0].message.tool_calls[0].function.arguments = '{"research_context": "Context", "research_landscape": "Landscape", "themes_text": [], "methodological_comparison": "Meth", "algorithm_model_comparison": "Alg", "findings_synthesis": "Find", "research_evolution": "Evo", "target_comparison": "Target", "similarities": [], "differences": [], "overall_synthesis": "Overall"}'
        mock_create.return_value = mock_response
        
        result = asyncio.run(generate_literature_survey(1))
        
        assert result["papers_used"] == 10
        assert mock_create.call_count == 1
        
        # Verify prompt received 10 papers
        called_prompt = mock_create.call_args[1]["messages"][0]["content"]
        assert "Paper ID: 1" in called_prompt
        assert "Paper ID: 10" in called_prompt

@pytest.mark.asyncio
async def test_structured_output_validation():
    # Test 5 & 7
    with patch("app.services.literature.literature_survey_service.SessionLocal") as mock_session:
        session_instance = mock_session.return_value
        session_instance.query.return_value.filter.return_value.first.return_value = ResearchProfile(paper_id=1)
        
        analyses = [LiteratureAnalysis(related_paper=RelatedPaper(id=1, title="Paper 1", relevance_score=99))]
        
        query_mock = session_instance.query.return_value
        query_mock = query_mock.join.return_value
        query_mock = query_mock.filter.return_value
        query_mock = query_mock.order_by.return_value
        query_mock.limit.return_value.all.return_value = analyses
        
        with patch("app.services.literature.literature_survey_service.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.tool_calls = [MagicMock()]
            
            mock_response.choices[0].message.tool_calls[0].function.arguments = '{"research_context": "Context", "research_landscape": "Landscape", "themes_text": ["Theme 1"], "methodological_comparison": "Meth", "algorithm_model_comparison": "Alg", "findings_synthesis": "Find", "research_evolution": "Evo", "target_comparison": "Target", "similarities": [], "differences": [], "overall_synthesis": "Overall"}'
            mock_create.return_value = mock_response
            
            # For existing query
            session_instance.query.return_value.filter.return_value.first.side_effect = [
                ResearchProfile(paper_id=1), # profile
                None # survey existing check
            ]
            
            res = await generate_literature_survey(1)
            assert res["status"] == "completed"
            assert res["themes_generated"] == 1
            
            added_survey = session_instance.add.call_args[0][0]
            assert added_survey.themes[0]["name"] == "Theme 1"

@pytest.mark.asyncio
async def test_malformed_llm_response(mock_db_session):
    # Test 6
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.return_value = ResearchProfile(paper_id=1)
    
    analyses = [LiteratureAnalysis(related_paper=RelatedPaper(id=1, title="Paper 1", relevance_score=99))]
    
    query_mock = session_instance.query.return_value
    query_mock = query_mock.join.return_value
    query_mock = query_mock.filter.return_value
    query_mock = query_mock.order_by.return_value
    query_mock.limit.return_value.all.return_value = analyses
    
    with patch("app.services.literature.literature_survey_service.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        mock_response.choices[0].message.tool_calls[0].function.arguments = "invalid json"
        mock_create.return_value = mock_response
        
        res = await generate_literature_survey(1)
        assert "error" in res

@pytest.mark.asyncio
async def test_idempotency_and_persistence(mock_db_session):
    # Test 9 and 10
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.return_value = ResearchProfile(paper_id=1)
    
    analyses = [LiteratureAnalysis(related_paper=RelatedPaper(id=1, title="Paper 1", relevance_score=99))]
    
    query_mock = session_instance.query.return_value
    query_mock = query_mock.join.return_value
    query_mock = query_mock.filter.return_value
    query_mock = query_mock.order_by.return_value
    query_mock.limit.return_value.all.return_value = analyses
    
    existing_survey = LiteratureSurvey(id=1, paper_id=1, research_context="Old Context")
    
    session_instance.query.return_value.filter.return_value.first.side_effect = [
        ResearchProfile(paper_id=1), # profile
        existing_survey # survey check
    ]
    
    with patch("app.services.literature.literature_survey_service.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        
        mock_response.choices[0].message.tool_calls[0].function.arguments = '{"research_context": "New Context", "research_landscape": "Landscape", "themes_text": [], "methodological_comparison": "Meth", "algorithm_model_comparison": "Alg", "findings_synthesis": "Find", "research_evolution": "Evo", "target_comparison": "Target", "similarities": [], "differences": [], "overall_synthesis": "Overall"}'
        mock_create.return_value = mock_response
        
        res = await generate_literature_survey(1)
        
        assert res["status"] == "completed"
        assert session_instance.add.call_count == 0 # Since it existed, it should update
        assert existing_survey.research_context == "New Context"

@pytest.mark.asyncio
async def test_llm_failure(mock_db_session):
    # Test 11
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.return_value = ResearchProfile(paper_id=1)
    
    analyses = [LiteratureAnalysis(related_paper=RelatedPaper(id=1, title="Paper 1", relevance_score=99))]
    
    query_mock = session_instance.query.return_value
    query_mock = query_mock.join.return_value
    query_mock = query_mock.filter.return_value
    query_mock = query_mock.order_by.return_value
    query_mock.limit.return_value.all.return_value = analyses
    
    with patch("app.services.literature.literature_survey_service.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = Exception("LLM connection error")
        
        res = await generate_literature_survey(1)
        assert "error" in res
        assert "LLM connection error" in res["error"]
        # Previous data is not deleted
        assert session_instance.delete.call_count == 0

@pytest.mark.asyncio
async def test_no_hallucinated_data(mock_db_session):
    # Test 8
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.return_value = ResearchProfile(paper_id=1)
    
    analyses = [LiteratureAnalysis(related_paper=RelatedPaper(id=1, title="Paper 1", relevance_score=99))]
    
    query_mock = session_instance.query.return_value
    query_mock = query_mock.join.return_value
    query_mock = query_mock.filter.return_value
    query_mock = query_mock.order_by.return_value
    query_mock.limit.return_value.all.return_value = analyses
    
    session_instance.query.return_value.filter.return_value.first.side_effect = [
        ResearchProfile(paper_id=1), # profile
        None # survey check
    ]
    
    with patch("app.services.literature.literature_survey_service.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        
        mock_response.choices[0].message.tool_calls[0].function.arguments = '{"research_context": "Context", "research_landscape": "Landscape", "themes_text": [], "methodological_comparison": "Meth", "algorithm_model_comparison": "Alg", "findings_synthesis": "Find", "research_evolution": "Not available from retrieved metadata", "target_comparison": "Target", "similarities": [], "differences": [], "overall_synthesis": "Overall"}'
        mock_create.return_value = mock_response
        
        res = await generate_literature_survey(1)
        
        assert res["status"] == "completed"
        added_survey = session_instance.add.call_args[0][0]
        assert added_survey.research_evolution == "Not available from retrieved metadata"

@pytest.mark.asyncio
async def test_empty_literature(mock_db_session):
    # Test 12
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.return_value = ResearchProfile(paper_id=1)
    
    # Mock literature analysis query
    query_mock = session_instance.query.return_value
    query_mock = query_mock.join.return_value
    query_mock = query_mock.filter.return_value
    query_mock = query_mock.order_by.return_value
    query_mock.limit.return_value.all.return_value = []
    
    result = await generate_literature_survey(1)
    assert "error" in result
    assert "Detailed literature analysis (Phase 7) must be completed" in result["error"]

@pytest.mark.asyncio
async def test_stringified_lists(mock_db_session):
    # Test 2 for Phase 8 Correction
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.return_value = ResearchProfile(paper_id=1)
    
    analyses = [LiteratureAnalysis(related_paper=RelatedPaper(id=1, title="Paper 1", relevance_score=99))]
    
    query_mock = session_instance.query.return_value
    query_mock = query_mock.join.return_value
    query_mock = query_mock.filter.return_value
    query_mock = query_mock.order_by.return_value
    query_mock.limit.return_value.all.return_value = analyses
    
    with patch("app.services.literature.literature_survey_service.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        
        # Simulating stringified array for themes_text
        mock_response.choices[0].message.tool_calls[0].function.arguments = '{"research_context": "Context", "research_landscape": "Landscape", "themes_text": "[\\"Theme 1\\", \\"Theme 2\\"]", "methodological_comparison": "Meth", "algorithm_model_comparison": "Alg", "findings_synthesis": "Find", "research_evolution": "Evo", "target_comparison": "Target", "similarities": "[\\"Sim 1\\"]", "differences": "[\\"Diff 1\\"]", "overall_synthesis": "Overall"}'
        mock_create.return_value = mock_response
        
        # For existing query
        session_instance.query.return_value.filter.return_value.first.side_effect = [
            ResearchProfile(paper_id=1), # profile
            None # survey existing check
        ]
        
        res = await generate_literature_survey(1)
        assert res["status"] == "completed"
        assert res["themes_generated"] == 2
        
        added_survey = session_instance.add.call_args[0][0]
        assert added_survey.themes[0]["name"] == "Theme 1"
        assert added_survey.themes[1]["name"] == "Theme 2"
        assert added_survey.similarities == ["Sim 1"]
        assert added_survey.differences == ["Diff 1"]

