import os
import sys
import time
import pytest
from unittest.mock import MagicMock, patch

# Align python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.tracer import LangfuseTracer, NoOpSpan, tracer
from core.logging_decorator import agent_logger
from services.llm_service import LLMService


def test_tracer_disabled_by_default():
    """Verify that tracer starts in no-op mode when disabled or credentials absent."""
    local_tracer = LangfuseTracer()
    # By default in test environment, LANGFUSE_ENABLED is False
    assert local_tracer.is_enabled is False
    assert local_tracer.client is None

    # Context manager executes smoothly
    with local_tracer.trace_agent_execution("test_agent", "user_123") as ctx:
        ctx["output"] = {"success": True}
        assert ctx["agent_name"] == "test_agent"

    # Generation record completes without error
    local_tracer.record_llm_generation(
        name="test_gen",
        model="gemini/gemini-2.5-flash",
        prompt="Hello",
        output_text="World",
        duration=0.5,
    )


def test_tracer_enabled_with_mocked_langfuse():
    """Verify trace and span capture when Langfuse credentials are valid."""
    mock_langfuse_cls = MagicMock()
    mock_client = MagicMock()
    mock_trace = MagicMock()
    mock_span = MagicMock()

    mock_client.trace.return_value = mock_trace
    mock_trace.span.return_value = mock_span
    mock_langfuse_cls.return_value = mock_client

    with patch.dict(
        os.environ,
        {
            "LANGFUSE_ENABLED": "True",
            "LANGFUSE_PUBLIC_KEY": "pk-lf-test",
            "LANGFUSE_SECRET_KEY": "sk-lf-test",
            "LANGFUSE_HOST": "https://test.langfuse.com",
        },
    ):
        with patch("config.settings.LANGFUSE_ENABLED", True), \
             patch("config.settings.LANGFUSE_PUBLIC_KEY", "pk-lf-test"), \
             patch("config.settings.LANGFUSE_SECRET_KEY", "sk-lf-test"), \
             patch("config.settings.LANGFUSE_HOST", "https://test.langfuse.com"), \
             patch("langfuse.Langfuse", mock_langfuse_cls):

            active_tracer = LangfuseTracer()
            assert active_tracer.is_enabled is True

            # Test successful agent execution span
            with active_tracer.trace_agent_execution(
                agent_name="resume_agent",
                user_id="user_abc",
                input_metadata={"step": 1},
            ) as ctx:
                ctx["output"] = {"status": "ok"}

            mock_client.trace.assert_called_once()
            trace_call_kwargs = mock_client.trace.call_args[1]
            assert trace_call_kwargs["name"] == "agent:resume_agent"
            assert trace_call_kwargs["user_id"] == "user_abc"
            assert "resume_agent" in trace_call_kwargs["tags"]

            mock_trace.span.assert_called_once()
            mock_span.end.assert_called_once()
            end_kwargs = mock_span.end.call_args[1]
            assert end_kwargs["output"] == {"status": "ok"}
            assert "duration_seconds" in end_kwargs["metadata"]


def test_tracer_captures_errors_on_exception():
    """Verify that agent execution exceptions are recorded as ERROR spans and re-raised."""
    mock_client = MagicMock()
    mock_trace = MagicMock()
    mock_span = MagicMock()
    mock_client.trace.return_value = mock_trace
    mock_trace.span.return_value = mock_span

    with patch("config.settings.LANGFUSE_ENABLED", True), \
         patch("config.settings.LANGFUSE_PUBLIC_KEY", "pk-lf-test"), \
         patch("config.settings.LANGFUSE_SECRET_KEY", "sk-lf-test"), \
         patch("langfuse.Langfuse", return_value=mock_client):

        active_tracer = LangfuseTracer()

        with pytest.raises(RuntimeError, match="Agent internal failure"):
            with active_tracer.trace_agent_execution("failing_agent", "user_xyz"):
                raise RuntimeError("Agent internal failure")

        mock_span.end.assert_called_once()
        end_kwargs = mock_span.end.call_args[1]
        assert end_kwargs["level"] == "ERROR"
        assert "Agent internal failure" in end_kwargs["status_message"]


def test_tracer_records_llm_generation_with_real_tokens():
    """Verify token counts are preserved and not fabricated."""
    mock_client = MagicMock()

    with patch("config.settings.LANGFUSE_ENABLED", True), \
         patch("config.settings.LANGFUSE_PUBLIC_KEY", "pk-test"), \
         patch("config.settings.LANGFUSE_SECRET_KEY", "sk-test"), \
         patch("langfuse.Langfuse", return_value=mock_client):

        active_tracer = LangfuseTracer()

        # Call with real exposed token counts
        active_tracer.record_llm_generation(
            name="llm:gemini",
            model="gemini/gemini-2.5-flash",
            prompt="Analyze resume",
            output_text="Analysis complete",
            duration=1.23,
            usage={"prompt_tokens": 150, "completion_tokens": 50, "total_tokens": 200},
            cost=0.00045,
        )

        mock_client.generation.assert_called_once()
        call_kwargs = mock_client.generation.call_args[1]
        assert call_kwargs["name"] == "llm:gemini"
        assert call_kwargs["model"] == "gemini/gemini-2.5-flash"
        assert call_kwargs["usage"]["input"] == 150
        assert call_kwargs["usage"]["output"] == 50
        assert call_kwargs["usage"]["total"] == 200
        assert call_kwargs["cost"] == 0.00045


def test_tracer_handles_missing_token_counts_without_fabrication():
    """Verify that when provider does not expose token usage or cost, none are fabricated."""
    mock_client = MagicMock()

    with patch("config.settings.LANGFUSE_ENABLED", True), \
         patch("config.settings.LANGFUSE_PUBLIC_KEY", "pk-test"), \
         patch("config.settings.LANGFUSE_SECRET_KEY", "sk-test"), \
         patch("langfuse.Langfuse", return_value=mock_client):

        active_tracer = LangfuseTracer()

        # Provider response without usage or cost
        active_tracer.record_llm_generation(
            name="llm:ollama",
            model="ollama/llama3",
            prompt="Test prompt",
            output_text="Test response",
            duration=0.8,
            usage=None,
            cost=None,
        )

        mock_client.generation.assert_called_once()
        call_kwargs = mock_client.generation.call_args[1]
        assert "usage" not in call_kwargs
        assert "cost" not in call_kwargs


def test_agent_logger_decorator_integrates_with_tracer():
    """Verify @agent_logger executes decorated function and integrates with tracer."""
    @agent_logger("test_mock_agent")
    def sample_agent_node(state: dict) -> dict:
        return {"routing_destination": "next_node", "last_response": "done"}

    result = sample_agent_node({"user_id": "test_user_42"})
    assert result["routing_destination"] == "next_node"
    assert result["last_response"] == "done"
