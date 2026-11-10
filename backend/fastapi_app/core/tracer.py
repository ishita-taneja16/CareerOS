import os
import time
import logging
from typing import Optional, Dict, Any, Union
from contextlib import contextmanager

from config import settings

logger = logging.getLogger(__name__)


class NoOpSpan:
    """Safe no-op span implementation used when Langfuse is disabled or unavailable."""

    def __init__(self, name: str = "noop"):
        self.name = name

    def end(self, *args, **kwargs):
        pass

    def update(self, *args, **kwargs):
        return self

    def event(self, *args, **kwargs):
        return self

    def generation(self, *args, **kwargs):
        return self

    def span(self, *args, **kwargs):
        return self


class LangfuseTracer:
    """
    Production-grade Langfuse observability manager for CareerOS multi-agent workflows.
    Provides tracing and span tracking for agent execution nodes, latencies,
    routing steps, errors, and LLM token usage/costs.
    Degrades gracefully to No-Op if disabled or credentials are not supplied.
    """

    def __init__(self):
        self._client = None
        self._enabled = False
        self._initialize_client()

    def _initialize_client(self):
        enabled_setting = getattr(settings, "LANGFUSE_ENABLED", False)
        public_key = getattr(settings, "LANGFUSE_PUBLIC_KEY", "") or os.environ.get("LANGFUSE_PUBLIC_KEY", "")
        secret_key = getattr(settings, "LANGFUSE_SECRET_KEY", "") or os.environ.get("LANGFUSE_SECRET_KEY", "")
        host = getattr(settings, "LANGFUSE_HOST", "https://cloud.langfuse.com") or os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")

        if not enabled_setting or not public_key or not secret_key:
            logger.info("Langfuse tracing is disabled or credentials are not configured. Running in No-Op mode.")
            self._enabled = False
            self._client = None
            return

        try:
            import langfuse
            self._client = langfuse.Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=host,
            )
            self._enabled = True
            logger.info(f"Langfuse tracing initialized successfully (host: {host}).")
        except Exception as e:
            logger.warning(f"Failed to initialize Langfuse client: {e}. Falling back to No-Op mode.")
            self._enabled = False
            self._client = None

    @property
    def is_enabled(self) -> bool:
        return self._enabled and self._client is not None

    @property
    def client(self):
        return self._client

    @contextmanager
    def trace_agent_execution(
        self,
        agent_name: str,
        user_id: str = "unknown",
        session_id: Optional[str] = None,
        input_metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Context manager to capture a trace or span for an agent workflow node.
        Measures duration, input/output state, routing, and records exceptions.
        """
        start_time = time.time()
        trace_obj = None
        span_obj = None

        if self.is_enabled:
            try:
                trace_obj = self._client.trace(
                    name=f"agent:{agent_name}",
                    user_id=user_id,
                    session_id=session_id,
                    metadata=input_metadata or {},
                    tags=["careeros", "agent", agent_name],
                )
                span_obj = trace_obj.span(
                    name=agent_name,
                    input=input_metadata or {},
                )
            except Exception as e:
                logger.debug(f"Langfuse span creation error: {e}")
                span_obj = NoOpSpan(agent_name)
        else:
            span_obj = NoOpSpan(agent_name)

        context_data = {
            "agent_name": agent_name,
            "user_id": user_id,
            "output": None,
            "error": None,
        }

        try:
            yield context_data
            duration = time.time() - start_time
            if self.is_enabled and span_obj and not isinstance(span_obj, NoOpSpan):
                try:
                    span_obj.end(
                        output=context_data.get("output"),
                        metadata={"duration_seconds": round(duration, 4)},
                    )
                except Exception as ex:
                    logger.debug(f"Langfuse span end error: {ex}")
        except Exception as err:
            duration = time.time() - start_time
            context_data["error"] = str(err)
            if self.is_enabled and span_obj and not isinstance(span_obj, NoOpSpan):
                try:
                    span_obj.end(
                        level="ERROR",
                        status_message=str(err),
                        metadata={"duration_seconds": round(duration, 4), "error": str(err)},
                    )
                except Exception as ex:
                    logger.debug(f"Langfuse span error end error: {ex}")
            raise err

    def record_llm_generation(
        self,
        name: str,
        model: str,
        prompt: Union[str, list],
        output_text: str,
        duration: float,
        usage: Optional[Dict[str, Any]] = None,
        cost: Optional[float] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ):
        """
        Records an LLM generation step with input, output, duration, and token usage.
        Does NOT fabricate missing token or cost data.
        """
        if not self.is_enabled:
            return

        try:
            usage_dict = None
            if usage:
                # Capture actual exposed token counts
                prompt_tokens = usage.get("prompt_tokens") or usage.get("input_tokens")
                completion_tokens = usage.get("completion_tokens") or usage.get("output_tokens")
                total_tokens = usage.get("total_tokens")
                if total_tokens is None and prompt_tokens is not None and completion_tokens is not None:
                    total_tokens = prompt_tokens + completion_tokens

                usage_dict = {
                    k: v
                    for k, v in {
                        "input": prompt_tokens,
                        "output": completion_tokens,
                        "total": total_tokens,
                        "unit": "TOKENS",
                    }.items()
                    if v is not None
                }

            generation_params = {
                "name": name,
                "model": model,
                "input": prompt,
                "output": output_text,
                "metadata": metadata or {},
            }
            if usage_dict:
                generation_params["usage"] = usage_dict
            if cost is not None:
                generation_params["cost"] = cost
            if error:
                generation_params["level"] = "ERROR"
                generation_params["status_message"] = error

            if trace_id and hasattr(self._client, "generation"):
                generation_params["trace_id"] = trace_id

            self._client.generation(**generation_params)
        except Exception as e:
            logger.debug(f"Langfuse generation record error: {e}")

    def flush(self):
        """Flushes buffered traces to the Langfuse backend."""
        if self.is_enabled:
            try:
                self._client.flush()
            except Exception as e:
                logger.debug(f"Langfuse flush error: {e}")


# Singleton instance
tracer = LangfuseTracer()
