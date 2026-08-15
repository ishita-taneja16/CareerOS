import pytest
import os
import sys

# Align python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.llm_service import PROVIDERS, QwenProvider
from services.qwen_inference_service import qwen_service


def test_qwen_provider_registration():
    assert "qwen" in PROVIDERS
    provider = PROVIDERS["qwen"]
    assert isinstance(provider, QwenProvider)
    model, api_key = provider.get_model_and_key()
    assert "Qwen" in model


def test_qwen_service_defaults():
    litellm_model = qwen_service.get_litellm_model_string()
    assert "huggingface/Qwen" in litellm_model or "ollama" in litellm_model
