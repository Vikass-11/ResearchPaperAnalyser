import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.literature.research_gap_service import detect_research_gaps
from app.models.schema import RelatedPaper, ResearchProfile, LiteratureAnalysis, LiteratureSurvey, ResearchGap

@pytest.fixture
def mock_db_session():
    with patch("app.services.literature.research_gap_service.SessionLocal") as mock:
        yield mock

# 13. missing ResearchProfile
def test_missing_research_profile(mock_db_session):
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.return_value = None
    
    result = asyncio.run(detect_research_gaps(1))
    assert "error" in result
    assert "Research profile must be generated" in result["error"]

# 14. missing LiteratureSurvey
def test_missing_literature_survey(mock_db_session):
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.side_effect = [
        ResearchProfile(paper_id=1), # profile found
        None # survey missing
    ]
    
    result = asyncio.run(detect_research_gaps(1))
    assert "error" in result
    assert "Literature survey (Phase 8) must be completed" in result["error"]

# Helper to mock db setup
def setup_mock_db(session_instance, num_analyses=1):
    profile = ResearchProfile(paper_id=1, research_topic="Topic")
    survey = LiteratureSurvey(paper_id=1, research_context="Context", themes=[{"name": "Theme"}])
    analyses = [
        LiteratureAnalysis(
            related_paper=RelatedPaper(id=i, title=f"Paper {i}", relevance_score=100-i)
        ) for i in range(1, num_analyses + 1)
    ]
    
    session_instance.query.return_value.filter.return_value.first.side_effect = [profile, survey]
    
    query_mock = session_instance.query.return_value
    query_mock = query_mock.join.return_value
    query_mock = query_mock.filter.return_value
    query_mock = query_mock.order_by.return_value
    query_mock.limit.return_value.all.return_value = analyses

# 1. schema validation & 4. flat LLM response parsing & 11. related paper ID traceability
@pytest.mark.asyncio
async def test_successful_parsing_and_traceability(mock_db_session):
    session_instance = mock_db_session.return_value
    setup_mock_db(session_instance, 1)
    
    with patch("app.services.literature.research_gap_service.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        mock_response.choices[0].message.tool_calls[0].function.arguments = '''
        {
            "gaps": [
                {
                    "gap_type": "Methodological Gap",
                    "title": "Test Gap",
                    "description": "Valid description",
                    "evidence": ["Seen in Paper 1"],
                    "significance": "High",
                    "confidence": 0.8,
                    "proposed_direction": "Do this"
                }
            ]
        }
        '''
        mock_create.return_value = mock_response
        
        res = await detect_research_gaps(1)
        assert res["generated"] is True
        
        # Verify db.add was called
        added_gap = session_instance.add.call_args[0][0]
        assert added_gap.title == "Test Gap"
        assert added_gap.related_paper_ids == [1] # Traceability success
        assert added_gap.confidence == 0.8

# 2. confidence validation
@pytest.mark.asyncio
async def test_confidence_validation(mock_db_session):
    session_instance = mock_db_session.return_value
    setup_mock_db(session_instance, 1)
    
    with patch("app.services.literature.research_gap_service.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        mock_response.choices[0].message.tool_calls[0].function.arguments = '''
        {
            "gaps": [
                {
                    "gap_type": "Dataset Gap",
                    "title": "Gap 1",
                    "description": "Desc 1",
                    "evidence": ["E1"],
                    "confidence": 1.5,
                    "proposed_direction": "Dir 1"
                },
                {
                    "gap_type": "Dataset Gap",
                    "title": "Gap 2",
                    "description": "Desc 2",
                    "evidence": ["E2"],
                    "confidence": -0.5,
                    "proposed_direction": "Dir 2"
                },
                {
                    "gap_type": "Dataset Gap",
                    "title": "Gap 3",
                    "description": "Desc 3",
                    "evidence": ["E3"],
                    "confidence": 0.9,
                    "proposed_direction": "Dir 3"
                }
            ]
        }
        '''
        mock_create.return_value = mock_response
        
        res = await detect_research_gaps(1)
        assert res["generated"] is True
        assert len(res["gaps"]) == 1
        assert res["gaps"][0]["title"] == "Gap 3"

# 3. stringified list normalization
@pytest.mark.asyncio
async def test_stringified_evidence_normalization(mock_db_session):
    session_instance = mock_db_session.return_value
    setup_mock_db(session_instance, 1)
    
    with patch("app.services.literature.research_gap_service.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        mock_response.choices[0].message.tool_calls[0].function.arguments = '''
        {
            "gaps": [
                {
                    "gap_type": "Temporal Gap",
                    "title": "Old Data",
                    "description": "Desc",
                    "evidence": "[\\"ev 1\\", \\"ev 2\\"]",
                    "confidence": 0.5,
                    "proposed_direction": "Dir"
                }
            ]
        }
        '''
        mock_create.return_value = mock_response
        
        res = await detect_research_gaps(1)
        assert res["generated"] is True
        added_gap = session_instance.add.call_args[0][0]
        assert len(added_gap.evidence) == 2
        assert added_gap.evidence[0] == "ev 1"

# 5. malformed response handling & 15. LLM failure isolation
@pytest.mark.asyncio
async def test_malformed_response_handling(mock_db_session):
    session_instance = mock_db_session.return_value
    setup_mock_db(session_instance, 1)
    
    with patch("app.services.literature.research_gap_service.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        mock_response.choices[0].message.tool_calls[0].function.arguments = 'invalid json'
        mock_create.return_value = mock_response
        
        res = await detect_research_gaps(1)
        assert "error" in res
        # Ensure it didn't crash pipeline
        assert session_instance.delete.call_count == 0

# 6. empty response handling
@pytest.mark.asyncio
async def test_empty_response_handling(mock_db_session):
    session_instance = mock_db_session.return_value
    setup_mock_db(session_instance, 1)
    
    with patch("app.services.literature.research_gap_service.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        mock_response.choices[0].message.tool_calls[0].function.arguments = '{"gaps": []}'
        mock_create.return_value = mock_response
        
        res = await detect_research_gaps(1)
        assert res["generated"] is True
        assert len(res["gaps"]) == 0

# 7. duplicate gap removal
@pytest.mark.asyncio
async def test_duplicate_gap_removal(mock_db_session):
    session_instance = mock_db_session.return_value
    setup_mock_db(session_instance, 1)
    
    with patch("app.services.literature.research_gap_service.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        mock_response.choices[0].message.tool_calls[0].function.arguments = '''
        {
            "gaps": [
                {
                    "gap_type": "Other",
                    "title": "A  Gap!",
                    "description": "Desc 1",
                    "evidence": ["E1"],
                    "confidence": 0.5,
                    "proposed_direction": "D1"
                },
                {
                    "gap_type": "Other",
                    "title": "a gap",
                    "description": "Desc 2",
                    "evidence": ["E2"],
                    "confidence": 0.5,
                    "proposed_direction": "D2"
                }
            ]
        }
        '''
        mock_create.return_value = mock_response
        
        res = await detect_research_gaps(1)
        assert res["generated"] is True
        assert len(res["gaps"]) == 1
        assert session_instance.add.call_count == 1

# 8. invalid gap filtering (empty title/desc) & 10. evidence validation
@pytest.mark.asyncio
async def test_invalid_gap_filtering(mock_db_session):
    session_instance = mock_db_session.return_value
    setup_mock_db(session_instance, 1)
    
    with patch("app.services.literature.research_gap_service.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        mock_response.choices[0].message.tool_calls[0].function.arguments = '''
        {
            "gaps": [
                {
                    "gap_type": "Other",
                    "title": "",
                    "description": "Missing title",
                    "evidence": ["E"],
                    "confidence": 0.5,
                    "proposed_direction": "D"
                },
                {
                    "gap_type": "Other",
                    "title": "Missing desc",
                    "description": "",
                    "evidence": ["E"],
                    "confidence": 0.5,
                    "proposed_direction": "D"
                },
                {
                    "gap_type": "Other",
                    "title": "Missing evidence",
                    "description": "Desc",
                    "evidence": [],
                    "confidence": 0.5,
                    "proposed_direction": "D"
                },
                {
                    "gap_type": "Other",
                    "title": "Generic",
                    "description": "More research is needed",
                    "evidence": ["E"],
                    "confidence": 0.5,
                    "proposed_direction": "D"
                }
            ]
        }
        '''
        mock_create.return_value = mock_response
        
        res = await detect_research_gaps(1)
        assert res["generated"] is True
        assert len(res["gaps"]) == 0

# 9. unsupported gap filtering
@pytest.mark.asyncio
async def test_unsupported_gap_filtering(mock_db_session):
    session_instance = mock_db_session.return_value
    setup_mock_db(session_instance, 1)
    
    with patch("app.services.literature.research_gap_service.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        mock_response.choices[0].message.tool_calls[0].function.arguments = '''
        {
            "gaps": [
                {
                    "gap_type": "Unsupported Type Random",
                    "title": "T1",
                    "description": "Desc",
                    "evidence": ["E1"],
                    "confidence": 0.5,
                    "proposed_direction": "D"
                }
            ]
        }
        '''
        mock_create.return_value = mock_response
        
        res = await detect_research_gaps(1)
        assert res["generated"] is True
        assert len(res["gaps"]) == 1
        added_gap = session_instance.add.call_args[0][0]
        assert added_gap.gap_type == "Other"

# 12. idempotency
@pytest.mark.asyncio
async def test_idempotency(mock_db_session):
    session_instance = mock_db_session.return_value
    setup_mock_db(session_instance, 1)
    
    with patch("app.services.literature.research_gap_service.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        mock_response.choices[0].message.tool_calls[0].function.arguments = '''
        {
            "gaps": [
                {
                    "gap_type": "Other",
                    "title": "T1",
                    "description": "Desc",
                    "evidence": ["E1"],
                    "confidence": 0.5,
                    "proposed_direction": "D"
                }
            ]
        }
        '''
        mock_create.return_value = mock_response
        
        res = await detect_research_gaps(1)
        assert res["generated"] is True
        assert session_instance.query.return_value.filter.return_value.delete.call_count == 1

# 16. no hallucinated paper IDs
@pytest.mark.asyncio
async def test_no_hallucinated_paper_ids(mock_db_session):
    session_instance = mock_db_session.return_value
    setup_mock_db(session_instance, 1)
    
    with patch("app.services.literature.research_gap_service.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        mock_response.choices[0].message.tool_calls[0].function.arguments = '''
        {
            "gaps": [
                {
                    "gap_type": "Other",
                    "title": "T1",
                    "description": "Desc",
                    "evidence": ["Evidence pointing to non-existent paper 999"],
                    "confidence": 0.5,
                    "proposed_direction": "D"
                }
            ]
        }
        '''
        mock_create.return_value = mock_response
        
        res = await detect_research_gaps(1)
        assert res["generated"] is True
        added_gap = session_instance.add.call_args[0][0]
        assert added_gap.related_paper_ids == []

# 17. pipeline failure isolation
@pytest.mark.asyncio
async def test_pipeline_failure_isolation(mock_db_session):
    session_instance = mock_db_session.return_value
    setup_mock_db(session_instance, 1)
    
    with patch("app.services.literature.research_gap_service.client.chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = Exception("LLM connection error")
        
        res = await detect_research_gaps(1)
        assert "error" in res
        assert "LLM connection error" in res["error"]
        assert session_instance.delete.call_count == 0
