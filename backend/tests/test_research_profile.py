import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from app.schemas.literature import ResearchProfileSchema
from app.services.literature.research_profile_service import generate_research_profile, normalize_list_field

def test_normalize_list_field():
    # 1. Proper Python arrays
    assert normalize_list_field(["a", "b"]) == ["a", "b"]
    
    # 2. "[]" string
    assert normalize_list_field("[]") == []
    
    # 3. JSON array string
    assert normalize_list_field('["CNN", "ResNet"]') == ["CNN", "ResNet"]
    
    # 4. comma-separated string
    assert normalize_list_field("CNN, ResNet") == ["CNN", "ResNet"]
    
    # 5. empty string
    assert normalize_list_field("") == []
    assert normalize_list_field("   ") == []
    
    # 6. null
    assert normalize_list_field(None) == []
    assert normalize_list_field("null") == []
    assert normalize_list_field("NULL") == []
    
    # 7. invalid value
    assert normalize_list_field("invalid string with spaces") == ["invalid string with spaces"]
    
    # 8. mixed valid/invalid fields
    assert normalize_list_field("Valid, , Invalid, 123") == ["Valid", "Invalid", "123"]

@pytest.fixture
def mock_db_session():
    with patch("app.services.literature.research_profile_service.SessionLocal") as mock:
        yield mock

@pytest.fixture
def mock_openai():
    with patch("app.services.literature.research_profile_service.client") as mock:
        yield mock

@pytest.mark.asyncio
async def test_generate_research_profile_paper_not_found(mock_db_session):
    # Setup mock
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.return_value = None
    
    result = await generate_research_profile(999)
    assert result is None

@pytest.mark.asyncio
async def test_generate_research_profile_success(mock_db_session, mock_openai):
    # Mock Paper
    mock_paper = MagicMock()
    mock_paper.title = "Test Deep Learning"
    mock_paper.sections = []
    mock_paper.contributions = []
    
    session_instance = mock_db_session.return_value
    session_instance.query.return_value.filter.return_value.first.side_effect = [mock_paper, None]
    
    # Mock LLM Response
    mock_response = MagicMock()
    mock_tool_call = MagicMock()
    mock_tool_call.function.arguments = '{"research_domain": "Computer Science", "sub_domains": ["AI"], "research_topic": "Test Topic", "research_problem": "Problem", "research_objective": "Objective", "methodology": "Method", "methods": [], "algorithms": [], "models": [], "technologies": [], "datasets": [], "key_concepts": [], "keywords": ["test", "ai"], "research_questions": [], "application_domain": "Healthcare"}'
    mock_response.choices = [MagicMock(message=MagicMock(tool_calls=[mock_tool_call]))]
    
    mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
    
    result = await generate_research_profile(1)
    
    assert isinstance(result, ResearchProfileSchema)
    assert result.research_domain == "Computer Science"
    assert "test" in result.keywords
