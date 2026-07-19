import os
import time
import logging
import contextvars
from typing import Optional, Union, Type, Dict, Any
from pydantic import BaseModel
from litellm import completion
from config import settings

logger = logging.getLogger(__name__)

# Context variable to hold retry count during thread/task execution
llm_retry_count_var = contextvars.ContextVar("llm_retry_count", default=0)

class LLMProvider:
    """Base class for implementing specific LLM providers."""
    def get_model_and_key(self) -> tuple[str, Optional[str]]:
        raise NotImplementedError()

class GeminiProvider(LLMProvider):
    def get_model_and_key(self) -> tuple[str, Optional[str]]:
        model = settings.LLM_MODEL or "gemini/gemini-2.5-flash"
        return model, settings.GEMINI_API_KEY

class OllamaProvider(LLMProvider):
    def get_model_and_key(self) -> tuple[str, Optional[str]]:
        model = settings.LLM_MODEL or "ollama/llama3"
        return model, None

class HuggingFaceProvider(LLMProvider):
    def get_model_and_key(self) -> tuple[str, Optional[str]]:
        model = settings.LLM_MODEL or f"huggingface/{os.environ.get('HF_MODEL_NAME', 'meta-llama/Meta-Llama-3-8B-Instruct')}"
        return model, os.environ.get("HUGGINGFACE_API_KEY", "")

# Registry for easy extensibility of future model providers
PROVIDERS: Dict[str, LLMProvider] = {
    "gemini": GeminiProvider(),
    "ollama": OllamaProvider(),
    "huggingface": HuggingFaceProvider()
}

class LLMService:
    @staticmethod
    def call(
        prompt: str,
        system_prompt: Optional[str] = None,
        response_format: Optional[Union[Type[BaseModel], Dict[str, Any]]] = None,
        retries: int = 3,
        timeout: int = 30,
        provider: Optional[str] = None
    ) -> str:
        """
        Centralized LLM runner wrapping LiteLLM. Automatically implements provider routing,
        timeout controls, structured response mapping, and exponential backoff retry algorithms.
        """
        active_provider_name = provider or settings.LLM_PROVIDER or "gemini"
        active_provider = active_provider_name.lower().strip()

        provider_impl = PROVIDERS.get(active_provider, PROVIDERS["gemini"])
        model, api_key = provider_impl.get_model_and_key()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        last_exception = None
        delay = 1.0

        for attempt in range(retries):
            start = time.time()
            try:
                response = completion(
                    model=model,
                    messages=messages,
                    api_key=api_key,
                    timeout=timeout,
                    response_format=response_format
                )
                duration = time.time() - start
                logger.info(
                    f"LLM Success | Model: {model} | Time: {duration:.2f}s | Attempt: {attempt + 1}"
                )
                return response.choices[0].message.content
            except Exception as e:
                duration = time.time() - start
                if attempt < retries - 1:
                    llm_retry_count_var.set(llm_retry_count_var.get() + 1)

                logger.warning(
                    f"LLM Attempt failed | Model: {model} | Duration: {duration:.2f}s | "
                    f"Attempt: {attempt + 1}/{retries} | Error: {str(e)}"
                )
                last_exception = e
                if attempt < retries - 1:
                    time.sleep(delay)
                    delay *= 2

        raise last_exception
