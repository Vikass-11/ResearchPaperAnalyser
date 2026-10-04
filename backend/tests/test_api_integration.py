import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.database import engine, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import EVERYTHING so Base knows all tables before create_all
from app.models.schema import Base, Paper, ResearchProfile, RelatedPaper, LiteratureAnalysis, LiteratureSurvey, ResearchGap, RecentResearch

from sqlalchemy.pool import StaticPool

# Setup test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine_test = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

Base.metadata.create_all(bind=engine_test)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine_test)
    Base.metadata.create_all(bind=engine_test)
    
    db = TestingSessionLocal()
    # Add dummy paper
    p = Paper(id=1, title="Test", file_path="test.pdf", processing_status="COMPLETED")
    db.add(p)
    rp = ResearchProfile(paper_id=1, research_topic="Test Topic")
    db.add(rp)
    db.commit()
    db.close()
    
def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"

def test_get_paper_not_found():
    response = client.get("/api/v1/papers/999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PAPER_NOT_FOUND"

def test_get_paper_success():
    response = client.get("/api/v1/papers/1")
    assert response.status_code == 200

def test_research_profile_endpoint():
    response = client.get("/api/v1/papers/1/literature/research-profile")
    assert response.status_code == 200
    data = response.json()
    assert "research_profile" in data
    assert data["research_profile"]["research_topic"] == "Test Topic"

def test_pipeline_status():
    response = client.get("/api/v1/papers/1/pipeline/status")
    assert response.status_code == 200
    data = response.json()
    assert "stages" in data
    assert data["status"] == "completed"
    assert data["stages"]["research_profile"]["status"] == "completed"
    assert data["stages"]["related_papers"]["status"] == "pending"

def test_research_summary():
    response = client.get("/api/v1/papers/1/research-summary")
    assert response.status_code == 200
    data = response.json()
    assert data["paper"]["id"] == 1
    assert data["literature"]["related_count"] == 0

def test_delete_paper():
    response = client.delete("/api/v1/papers/1")
    assert response.status_code == 200
    
    # Verify it is deleted
    response2 = client.get("/api/v1/papers/1")
    assert response2.status_code == 404

def test_pagination():
    response = client.get("/api/v1/papers?page=1&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert data["limit"] == 5
    assert "items" in data

def test_openapi_json():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "/api/v1/papers/{paper_id}/research-summary" in data["paths"]
