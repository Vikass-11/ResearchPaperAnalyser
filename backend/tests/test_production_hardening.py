import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import MAX_UPLOAD_SIZE_BYTES
import os

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "llm" in data

def test_upload_validation_non_pdf():
    # Attempt to upload a text file
    files = {"file": ("test.txt", b"dummy content", "text/plain")}
    response = client.post("/api/v1/papers/upload", files=files)
    assert response.status_code == 400
    assert "error" in response.json()
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

def test_upload_validation_size_limit():
    # We mock a large file upload
    large_content = b"0" * (MAX_UPLOAD_SIZE_BYTES + 1024)
    files = {"file": ("large.pdf", large_content, "application/pdf")}
    response = client.post("/api/v1/papers/upload", files=files)
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"

def test_api_limit_validation():
    # limit > 100 should be rejected
    response = client.get("/api/v1/papers/?limit=200")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

def test_api_page_validation():
    # page < 1 should be rejected
    response = client.get("/api/v1/papers/?page=0")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

def test_security_headers():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

def test_cors_headers():
    # Simulate an OPTIONS request for CORS
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET",
    }
    response = client.options("/api/v1/health", headers=headers)
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
