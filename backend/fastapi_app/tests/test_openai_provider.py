import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Align python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import settings
from services.llm_service import PROVIDERS, OpenAIProvider, LLMService
from ml.evaluation.eval_framework import run_comparative_benchmark


def test_openai_provider_registration():
    """Verify OpenAI provider is properly registered in PROVIDERS dictionary."""
    assert "openai" in PROVIDERS
    provider = PROVIDERS["openai"]
    assert isinstance(provider, OpenAIProvider)

    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-mock-key"}):
        with patch.object(settings, "OPENAI_API_KEY", "sk-test-mock-key"):
            with patch.object(settings, "OPENAI_MODEL", "gpt-4o-mini"):
                model, api_key = provider.get_model_and_key()
                assert model == "openai/gpt-4o-mini"
                assert api_key == "sk-test-mock-key"


def test_openai_provider_selection_and_execution_mocked():
    """Verify provider selection routes to OpenAI and completes without paid API calls."""
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = "OpenAI response to candidate"
    mock_resp.usage = {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20}

    with patch("services.llm_service.completion", return_value=mock_resp) as mock_completion:
        with patch.object(settings, "OPENAI_API_KEY", "sk-mock-123"):
            content = LLMService.call(
                prompt="Review this resume bullet",
                provider="openai",
                retries=1
            )

            assert content == "OpenAI response to candidate"
            mock_completion.assert_called_once()
            call_kwargs = mock_completion.call_args[1]
            assert "openai" in call_kwargs["model"]
            assert call_kwargs["api_key"] == "sk-mock-123"


def test_openai_error_handling_and_retries_mocked():
    """Verify error handling catches and retries on transient failures."""
    with patch("services.llm_service.completion", side_effect=Exception("Rate limit reached: 429")):
        with patch("time.sleep"):  # Avoid test delays during backoff
            with pytest.raises(Exception, match="Rate limit reached"):
                LLMService.call(
                    prompt="Test rate limit prompt",
                    provider="openai",
                    retries=2
                )


def test_benchmark_with_openai_provider():
    """Verify the 11-category benchmark runs with the OpenAI provider without paid API calls."""
    res = run_comparative_benchmark(providers=["openai"], save_results=False)
    assert res["status"] == "completed"
    assert "openai" in res["provider_comparison"]
    openai_data = res["provider_comparison"]["openai"]
    assert openai_data["total_benchmark_cases"] == 12
    assert "overall_pass_rate" in openai_data
    assert "category_performance" in openai_data
    assert len(res["evaluated_categories"]) >= 11
