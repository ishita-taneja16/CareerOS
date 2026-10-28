import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Align python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import settings
from services.llm_service import (
    PROVIDERS,
    GeminiProvider,
    AzureOpenAIProvider,
    AzureFoundryProvider,
    LLMService
)
from agents.supervisor import run_supervisor
from agents.state import AgentState
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_azure_and_foundry_provider_registration():
    """Verify Azure OpenAI and Azure Foundry providers are properly registered."""
    assert "azure" in PROVIDERS
    assert "azure_openai" in PROVIDERS
    assert "foundry" in PROVIDERS
    assert "azure_foundry" in PROVIDERS
    assert "gemini" in PROVIDERS

    assert isinstance(PROVIDERS["azure"], AzureOpenAIProvider)
    assert isinstance(PROVIDERS["azure_openai"], AzureOpenAIProvider)
    assert isinstance(PROVIDERS["foundry"], AzureFoundryProvider)
    assert isinstance(PROVIDERS["azure_foundry"], AzureFoundryProvider)


def test_gemini_provider_selection_mocked():
    """Verify Gemini provider is selected and executed without live network requests."""
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = "Gemini career guidance"
    mock_resp.usage = {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25}

    with patch("services.llm_service.completion", return_value=mock_resp) as mock_completion:
        with patch.object(settings, "LLM_PROVIDER", "gemini"):
            with patch.object(settings, "GEMINI_API_KEY", "mock-gemini-key"):
                content = LLMService.call(
                    prompt="How do I prepare for a senior engineer interview?",
                    provider="gemini",
                    retries=1
                )
                assert content == "Gemini career guidance"
                mock_completion.assert_called_once()
                call_kwargs = mock_completion.call_args[1]
                assert "gemini" in call_kwargs["model"]
                assert call_kwargs["api_key"] == "mock-gemini-key"


def test_azure_provider_selection_and_parameter_mapping_mocked():
    """Verify Azure OpenAI provider maps deployment, api_base, and api_version accurately."""
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = "Azure OpenAI resume feedback"
    mock_resp.usage = {"prompt_tokens": 20, "completion_tokens": 30, "total_tokens": 50}

    with patch("services.llm_service.completion", return_value=mock_resp) as mock_completion:
        with patch.object(settings, "AZURE_OPENAI_ENDPOINT", "https://mock-careers-ai.openai.azure.com/"):
            with patch.object(settings, "AZURE_OPENAI_API_KEY", "mock-azure-key-12345"):
                with patch.object(settings, "AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini-prod"):
                    with patch.object(settings, "AZURE_OPENAI_API_VERSION", "2024-02-15-preview"):
                        content = LLMService.call(
                            prompt="Evaluate this resume bullet point",
                            provider="azure",
                            retries=1
                        )

                        assert content == "Azure OpenAI resume feedback"
                        mock_completion.assert_called_once()
                        call_kwargs = mock_completion.call_args[1]
                        assert call_kwargs["model"] == "azure/gpt-4o-mini-prod"
                        assert call_kwargs["api_key"] == "mock-azure-key-12345"
                        assert call_kwargs["api_base"] == "https://mock-careers-ai.openai.azure.com"
                        assert call_kwargs["api_version"] == "2024-02-15-preview"


def test_azure_provider_missing_api_key_raises_error():
    """Verify selecting Azure OpenAI with a missing API key raises a descriptive error."""
    with patch.object(settings, "AZURE_OPENAI_ENDPOINT", "https://mock.openai.azure.com"):
        with patch.object(settings, "AZURE_OPENAI_API_KEY", ""):
            with patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": ""}):
                with pytest.raises(ValueError, match="AZURE_OPENAI_API_KEY is not configured"):
                    LLMService.call(
                        prompt="Test missing key",
                        provider="azure",
                        retries=1
                    )


def test_azure_provider_missing_endpoint_raises_error():
    """Verify selecting Azure OpenAI with a missing endpoint raises a descriptive error."""
    with patch.object(settings, "AZURE_OPENAI_ENDPOINT", ""):
        with patch.object(settings, "AZURE_OPENAI_API_KEY", "some-mock-key"):
            with patch.dict(os.environ, {"AZURE_OPENAI_ENDPOINT": ""}):
                with pytest.raises(ValueError, match="AZURE_OPENAI_ENDPOINT is not configured"):
                    LLMService.call(
                        prompt="Test missing endpoint",
                        provider="azure",
                        retries=1
                    )


def test_azure_foundry_provider_selection_and_execution_mocked():
    """Verify Microsoft Azure AI Foundry model endpoint routing via OpenAI-compatible adapter."""
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = "Foundry Phi-4 output"
    mock_resp.usage = {"prompt_tokens": 15, "completion_tokens": 25, "total_tokens": 40}

    with patch("services.llm_service.completion", return_value=mock_resp) as mock_completion:
        with patch.object(settings, "AZURE_FOUNDRY_ENDPOINT", "https://phi-4-demo.eastus.models.ai.azure.com"):
            with patch.object(settings, "AZURE_FOUNDRY_API_KEY", "mock-foundry-token-999"):
                with patch.object(settings, "AZURE_FOUNDRY_MODEL", "Phi-4"):
                    content = LLMService.call(
                        prompt="Extract key skills",
                        provider="azure_foundry",
                        retries=1
                    )
                    assert content == "Foundry Phi-4 output"
                    mock_completion.assert_called_once()
                    call_kwargs = mock_completion.call_args[1]
                    assert call_kwargs["model"] == "openai/Phi-4"
                    assert call_kwargs["api_key"] == "mock-foundry-token-999"
                    assert "phi-4-demo" in call_kwargs["api_base"]


def test_azure_provider_error_handling_and_retry_backoff_mocked():
    """Verify retry logic on transient Azure rate limits or 5xx errors."""
    mock_failure = Exception("Azure OpenAI rate limit reached (status 429): Quota exceeded")

    with patch("services.llm_service.completion", side_effect=mock_failure):
        with patch.object(settings, "AZURE_OPENAI_ENDPOINT", "https://mock.openai.azure.com"):
            with patch.object(settings, "AZURE_OPENAI_API_KEY", "mock-key"):
                with patch("time.sleep"):  # Bypass backoff sleep during tests
                    with pytest.raises(Exception, match="429"):
                        LLMService.call(
                            prompt="Retry prompt",
                            provider="azure",
                            retries=2
                        )


def test_supervisor_agent_routing_with_azure_provider():
    """Verify LangGraph supervisor agent functions properly when using Azure OpenAI provider."""
    mock_response = '{"next_agent": "ats_agent", "reason": "Applicant wants ATS feedback"}'

    with patch("services.llm_service.LLMService.call", return_value=mock_response):
        state = AgentState(
            user_id="user_azure_test",
            messages=[{"role": "user", "content": "How is my ATS keyword match?"}]
        )
        decision = run_supervisor(state)

        assert decision["routing_destination"] == "ats_agent"
        assert decision["routing_pipeline"] == ["ats_agent"]


def test_chat_stream_endpoint_with_azure_mocked():
    """Verify the chat interaction endpoint streams SSE events with Azure configured."""
    payload = {
        "user_id": "test_azure_chat_user",
        "messages": [
            {
                "role": "user",
                "content": "Can you check my resume against this job?"
            }
        ],
        "structured_resume_data": {
            "contact_info": {
                "name": "Alex Smith",
                "email": "alex@example.com",
                "phone": "555-0100",
                "location": "Seattle, WA"
            },
            "skills": ["Python", "Azure", "FastAPI"],
            "experiences": [],
            "education": [],
            "projects": [],
            "certifications": [],
            "achievements": []
        }
    }

    mock_responses = [
        '{"next_agent":"advisor_agent","reason":"Career advice requested"}',
        "Here are recommendations tailored using Azure AI Copilot!"
    ]

    with patch("services.llm_service.LLMService.call", side_effect=mock_responses):
        response = client.post("/api/v1/chat/", json=payload)
        assert response.status_code == 200

        content = response.content.decode()
        assert "event: step" in content
        assert "advisor_agent" in content
        assert "event: message" in content
        assert "Azure AI Copilot" in content
