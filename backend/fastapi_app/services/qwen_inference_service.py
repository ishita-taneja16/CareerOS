import os
import logging
from typing import Optional, Dict, Any
from config import settings

logger = logging.getLogger(__name__)


class QwenInferenceService:
    """
    Inference wrapper service for Qwen LLMs (e.g. Qwen2.5-7B-Instruct and fine-tuned checkpoints).
    Supports local HuggingFace transformers pipelines, vLLM / Ollama local APIs,
    and LiteLLM integration.
    """

    def __init__(self, model_path: Optional[str] = None, inference_url: Optional[str] = None):
        self.model_path = model_path or settings.QWEN_MODEL_PATH or "Qwen/Qwen2.5-7B-Instruct"
        self.inference_url = inference_url or settings.QWEN_INFERENCE_URL

    def get_litellm_model_string(self) -> str:
        """
        Returns LiteLLM compatible provider string for Qwen.
        """
        if self.inference_url:
            # Point to local vLLM or Ollama OpenAI-compatible server
            return f"openai/{self.model_path}"
        elif self.model_path.startswith("ollama/") or self.model_path.startswith("huggingface/"):
            return self.model_path
        else:
            return f"huggingface/{self.model_path}"

    def get_api_base(self) -> Optional[str]:
        """
        Returns API base URL if hosting a local vLLM or OpenAI-compatible Qwen server.
        """
        return self.inference_url if self.inference_url else None


qwen_service = QwenInferenceService()
