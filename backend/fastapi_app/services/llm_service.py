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

    def get_completion_kwargs(self) -> Dict[str, Any]:
        """Optional provider-specific parameters for litellm.completion."""
        return {}

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

class OpenAIProvider(LLMProvider):
    def get_model_and_key(self) -> tuple[str, Optional[str]]:
        model = settings.LLM_MODEL or f"openai/{settings.OPENAI_MODEL}"
        api_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", "")
        return model, api_key

class AzureOpenAIProvider(LLMProvider):
    """
    Microsoft Azure OpenAI Service provider.
    Connects to Azure OpenAI deployments via LiteLLM's azure/ model prefix.
    Reads all credentials and endpoints exclusively from environment variables.
    """
    def get_model_and_key(self) -> tuple[str, Optional[str]]:
        deployment = (
            settings.LLM_MODEL
            or getattr(settings, "AZURE_OPENAI_DEPLOYMENT", "")
            or os.environ.get("AZURE_OPENAI_DEPLOYMENT", "")
            or "gpt-4o-mini"
        )
        model = f"azure/{deployment}"
        api_key = getattr(settings, "AZURE_OPENAI_API_KEY", "") or os.environ.get("AZURE_OPENAI_API_KEY", "")
        return model, api_key

    def get_completion_kwargs(self) -> Dict[str, Any]:
        endpoint = (
            getattr(settings, "AZURE_OPENAI_ENDPOINT", "")
            or os.environ.get("AZURE_OPENAI_ENDPOINT", "")
        )
        api_version = (
            getattr(settings, "AZURE_OPENAI_API_VERSION", "")
            or os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        )
        kwargs: Dict[str, Any] = {}
        if endpoint:
            kwargs["api_base"] = endpoint.rstrip("/")
        if api_version:
            kwargs["api_version"] = api_version
        return kwargs

class AzureFoundryProvider(LLMProvider):
    """
    Microsoft Azure AI Foundry provider (Serverless Model-as-a-Service & Managed endpoints).
    Supports models such as Phi-4, Mistral, and Llama-3.3 via OpenAI-compatible endpoints.
    """
    def get_model_and_key(self) -> tuple[str, Optional[str]]:
        model_name = (
            settings.LLM_MODEL
            or getattr(settings, "AZURE_FOUNDRY_MODEL", "")
            or os.environ.get("AZURE_FOUNDRY_MODEL", "Phi-4")
        )
        model = f"openai/{model_name}"
        api_key = getattr(settings, "AZURE_FOUNDRY_API_KEY", "") or os.environ.get("AZURE_FOUNDRY_API_KEY", "")
        return model, api_key

    def get_completion_kwargs(self) -> Dict[str, Any]:
        endpoint = (
            getattr(settings, "AZURE_FOUNDRY_ENDPOINT", "")
            or os.environ.get("AZURE_FOUNDRY_ENDPOINT", "")
        )
        kwargs: Dict[str, Any] = {}
        if endpoint:
            endpoint = endpoint.rstrip("/")
            if not endpoint.endswith("/models") and not endpoint.endswith("/v1"):
                kwargs["api_base"] = f"{endpoint}/models"
            else:
                kwargs["api_base"] = endpoint
        return kwargs

# Registry for easy extensibility of future model providers
PROVIDERS: Dict[str, LLMProvider] = {
    "gemini": GeminiProvider(),
    "openai": OpenAIProvider(),
    "azure": AzureOpenAIProvider(),
    "azure_openai": AzureOpenAIProvider(),
    "foundry": AzureFoundryProvider(),
    "azure_foundry": AzureFoundryProvider(),
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
        extra_kwargs = provider_impl.get_completion_kwargs() if hasattr(provider_impl, "get_completion_kwargs") else {}

        # Validate required configuration for Azure providers gracefully
        if active_provider in ["azure", "azure_openai"]:
            if not api_key:
                raise ValueError("Azure OpenAI provider selected, but AZURE_OPENAI_API_KEY is not configured.")
            if not extra_kwargs.get("api_base"):
                raise ValueError("Azure OpenAI provider selected, but AZURE_OPENAI_ENDPOINT is not configured.")
        elif active_provider in ["foundry", "azure_foundry"]:
            if not api_key:
                raise ValueError("Azure Foundry provider selected, but AZURE_FOUNDRY_API_KEY is not configured.")
            if not extra_kwargs.get("api_base"):
                raise ValueError("Azure Foundry provider selected, but AZURE_FOUNDRY_ENDPOINT is not configured.")

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
                    response_format=response_format,
                    **extra_kwargs
                )
                duration = time.time() - start
                content = response.choices[0].message.content

                # Extract token usage and cost without fabricating missing numbers
                usage_dict = None
                if hasattr(response, "usage") and response.usage:
                    u = response.usage
                    if isinstance(u, dict):
                        usage_dict = u
                    else:
                        usage_dict = {
                            "prompt_tokens": getattr(u, "prompt_tokens", None),
                            "completion_tokens": getattr(u, "completion_tokens", None),
                            "total_tokens": getattr(u, "total_tokens", None),
                        }

                cost_val = None
                try:
                    import litellm
                    cost_val = litellm.completion_cost(completion_response=response)
                except Exception:
                    cost_val = getattr(response, "_hidden_params", {}).get("response_cost")

                # Record generation in Langfuse
                try:
                    from core.tracer import tracer
                    tracer.record_llm_generation(
                        name=f"llm:{active_provider}",
                        model=model,
                        prompt=prompt,
                        output_text=content,
                        duration=duration,
                        usage=usage_dict,
                        cost=cost_val,
                        metadata={
                            "attempt": attempt + 1,
                            "provider": active_provider,
                            "has_system_prompt": bool(system_prompt)
                        }
                    )
                except Exception as te:
                    logger.debug(f"Tracer generation logging skipped: {te}")

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
                err_msg = str(e)
                err_type = type(e).__name__

                # Differentiate provider error categories
                if "auth" in err_msg.lower() or "key" in err_msg.lower() or "unauthorized" in err_msg.lower() or "401" in err_msg:
                    logger.error(f"LLM Authentication/API Key error for provider '{active_provider}': {err_msg}")
                elif "rate" in err_msg.lower() or "quota" in err_msg.lower() or "429" in err_msg:
                    logger.warning(f"LLM Rate limit / Quota exceeded for provider '{active_provider}': {err_msg}")
                elif "timeout" in err_msg.lower():
                    logger.warning(f"LLM Request timed out after {timeout}s for provider '{active_provider}': {err_msg}")
                elif "deploymentnotfound" in err_msg.lower() or "not found" in err_msg.lower() or "404" in err_msg:
                    logger.error(f"LLM Deployment or Model not found for provider '{active_provider}': {err_msg}")

                if attempt < retries - 1:
                    llm_retry_count_var.set(llm_retry_count_var.get() + 1)

                logger.warning(
                    f"LLM Attempt failed | Model: {model} | Duration: {duration:.2f}s | "
                    f"Attempt: {attempt + 1}/{retries} | Error [{err_type}]: {err_msg}"
                )
                last_exception = e

                # Record error in tracer if last attempt
                if attempt == retries - 1:
                    try:
                        from core.tracer import tracer
                        tracer.record_llm_generation(
                            name=f"llm:{active_provider}",
                            model=model,
                            prompt=prompt,
                            output_text="",
                            duration=duration,
                            error=err_msg,
                            metadata={
                                "attempts": retries,
                                "provider": active_provider,
                                "error_type": err_type
                            }
                        )
                    except Exception:
                        pass

                if attempt < retries - 1:
                    time.sleep(delay)
                    delay *= 2

        raise last_exception
