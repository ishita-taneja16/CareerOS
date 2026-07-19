import os
import sys
from unittest.mock import patch

from fastapi.testclient import TestClient

# Align python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from main import app

client = TestClient(app)


def test_read_root():
    """Verify root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_ats_evaluation():
    """Verify ATS scoring."""

    payload = {
        "resume": {
            "contact_info": {
                "name": "Jane Doe",
                "email": "jane@example.com",
                "phone": "123-456-7890",
                "location": "NY",
            },
            "skills": ["React", "Python", "FastAPI"],
            "experiences": [],
            "education": [],
            "projects": [],
            "certifications": [],
            "achievements": [],
        },
        "job_description": (
            "Seeking a developer who knows React, Python and FastAPI."
        ),
    }

    response = client.post("/api/v1/ats/evaluate", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert "ats_score" in data
    assert data["subscores"]["keyword_match"] > 50


def test_chat_interaction():
    """Verify chat endpoint streams a response."""

    payload = {
        "user_id": "test_user_123",
        "messages": [
            {
                "role": "user",
                "content": "How can I improve my projects?"
            }
        ],
        "structured_resume_data": {
            "contact_info": {
                "name": "Jane Doe",
                "email": "jane@example.com",
                "phone": "123-456-7890",
                "location": "NY",
            },
            "skills": ["React", "Python", "FastAPI"],
            "experiences": [],
            "education": [],
            "projects": [],
            "certifications": [],
            "achievements": [],
        },
    }

    mock_responses = [
        '{"next_agent":"advisor_agent","reason":"General career advice"}',
        "You can improve your projects by using active verbs and metrics!",
    ]

    with patch("services.llm_service.LLMService.call") as mock_call:
        mock_call.side_effect = mock_responses

        response = client.post("/api/v1/chat/", json=payload)

        assert response.status_code == 200

        content = response.content.decode()

        assert "event: step" in content
        assert "advisor_agent" in content
        assert "event: message" in content
        assert "improve your projects" in content