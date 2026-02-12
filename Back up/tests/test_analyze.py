from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_invalid_api_key():
    response = client.post("/analyze-product", json={"image_url": "http://example.com"}, headers={"X-API-Key": "bad"})
    assert response.status_code == 401

def test_invalid_url():
    response = client.post("/analyze-product", json={"image_url": "file://etc/passwd"}, headers={"X-API-Key": "client"})
    assert response.status_code == 400