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

class QwenProvider(LLMProvider):
    def get_model_and_key(self) -> tuple[str, Optional[str]]:
        model = settings.LLM_MODEL or f"huggingface/{settings.QWEN_MODEL_PATH}"
        return model, os.environ.get("HUGGINGFACE_API_KEY", "")

# Registry for easy extensibility of future model providers
PROVIDERS: Dict[str, LLMProvider] = {
    "gemini": GeminiProvider(),
    "ollama": OllamaProvider(),
    "huggingface": HuggingFaceProvider(),
    "qwen": QwenProvider()
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
        timeout controls, structured response mapping, Responsible AI guardrails, and exponential backoff retry algorithms.
        """
        # 1. Responsible AI Input Guardrail Check
        if getattr(settings, "ENABLE_RESPONSIBLE_AI_GUARDRAILS", False):
            try:
                from ml.responsible_ai import ResponsibleAIGuardrailManager
                guardrails = ResponsibleAIGuardrailManager(
                    enable_guardrails=True,
                    bias_threshold=getattr(settings, "BIAS_THRESHOLD", 0.15)
                )
                input_check = guardrails.validate_input(prompt)
                if not input_check.get("is_valid"):
                    raise ValueError(f"Responsible AI Guardrail Block: {input_check.get('reason')}")
            except Exception as ge:
                if isinstance(ge, ValueError):
                    raise ge
                logger.debug(f"Guardrail check skipped: {ge}")

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
                content = response.choices[0].message.content

                # 2. Responsible AI Output Guardrail Check
                if getattr(settings, "ENABLE_RESPONSIBLE_AI_GUARDRAILS", False):
                    try:
                        from ml.responsible_ai import ResponsibleAIGuardrailManager
                        guardrails = ResponsibleAIGuardrailManager(
                            enable_guardrails=True,
                            bias_threshold=getattr(settings, "BIAS_THRESHOLD", 0.15)
                        )
                        output_check = guardrails.validate_output(content)
                        if not output_check.get("is_safe"):
                            logger.warning(
                                f"Responsible AI Output Warning | Warnings: {output_check.get('warnings')}"
                            )
                    except Exception as ge:
                        logger.debug(f"Output guardrail audit skipped: {ge}")

                logger.info(
                    f"LLM Success | Model: {model} | Time: {duration:.2f}s | Attempt: {attempt + 1}"
                )
                return content
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
