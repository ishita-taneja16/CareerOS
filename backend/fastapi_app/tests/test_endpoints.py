import pytest
from fastapi.testclient import TestClient
import sys
import os

# Align python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import app
from models.resume_schema import ResumeSchema

client = TestClient(app)

def test_read_root():
    """Verify that root endpoint is active and returns healthy status."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_ats_evaluation():
    """Verify that custom ATS engine parses input structures and scores overlaps correctly."""
    payload = {
        "resume": {
            "contact_info": {
                "name": "Jane Doe",
                "email": "jane@example.com",
                "phone": "123-456-7890",
                "location": "NY"
            },
            "skills": ["React", "Python", "FastAPI"],
            "experiences": [],
            "education": [],
            "projects": [],
            "certifications": [],
            "achievements": []
        },
        "job_description": "Seeking a developer who knows React, Python and FastAPI. Needs 2 years experience."
    }
    response = client.post("/api/v1/ats/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "ats_score" in data
    assert data["subscores"]["keyword_match"] > 50.0 # Match should trigger on overlap

def test_chat_interaction():
    """Verify that chat streaming executes the graph sequentially through dispatcher."""
    payload = {
        "user_id": "test_user_123",
        "messages": [
            {"role": "user", "content": "How can I improve my projects?"}
        ],
        "structured_resume_data": {
            "contact_info": {
                "name": "Jane Doe",
                "email": "jane@example.com",
                "phone": "123-456-7890",
                "location": "NY"
            },
            "skills": ["React", "Python", "FastAPI"],
            "experiences": [],
            "education": [],
            "projects": [],
            "certifications": [],
            "achievements": []
        }
    }
    
    from unittest.mock import patch
    
    # We mock LLMService.call to return sequential mock responses for:
    # 1. Supervisor pipeline decision
    # 2. Memory extractor check
    # 3. Advisor Agent response
    mock_responses = [
        '{"routing_pipeline": ["memory_agent", "advisor_agent"], "reason": "Fetch memory and advise"}',
        'No new preferences.',
        'You can improve your projects by using active verbs and metrics!'
    ]
    
    with patch("services.llm_service.LLMService.call") as mock_call:
        mock_call.side_effect = mock_responses
        
        response = client.post("/api/v1/chat/", json=payload)
        assert response.status_code == 200
        
        content = response.content.decode()
        assert "event: step" in content
        assert "event: message" in content
        assert "advisor_agent" in content
        assert "improve your projects" in content

