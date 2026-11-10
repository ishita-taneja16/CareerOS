import time
import functools
import logging
from typing import Callable, Any
from config import settings
from services.llm_service import llm_retry_count_var
from core.logging_manager import StructuredLogger
from core.tracer import tracer

logger = logging.getLogger("agent_logger")

def agent_logger(agent_name: str) -> Callable:
    """
    Python decorator to enforce centralized logging and Langfuse tracing on agent node execution cycles.
    Captures duration, model configs, routing destinations, retries and exceptions.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            state = args[0] if args else None
            user_id = "unknown"
            input_meta = {}
            if state:
                if isinstance(state, dict):
                    user_id = state.get("user_id", "unknown")
                    input_meta = {
                        "routing_destination": state.get("routing_destination"),
                        "message_count": len(state.get("messages", [])),
                        "has_resume": bool(state.get("structured_resume_data")),
                    }
                else:
                    user_id = getattr(state, "user_id", "unknown")
                    input_meta = {
                        "routing_destination": getattr(state, "routing_destination", ""),
                        "message_count": len(getattr(state, "messages", [])),
                        "has_resume": bool(getattr(state, "structured_resume_data", None)),
                    }
            
            logger.info(f"===> [START] Node: {agent_name} | User: {user_id}")
            start_time = time.time()
            
            # Reset retry counter for this execution context
            token = llm_retry_count_var.set(0)
            model_used = (
                "gemini/gemini-2.5-flash"
                if settings.GEMINI_API_KEY
                else "ollama/llama3"
            )
            
            with tracer.trace_agent_execution(
                agent_name=agent_name,
                user_id=user_id,
                input_metadata=input_meta,
            ) as trace_ctx:
                try:
                    # Invoke underlying agent node
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time

                    # Fetch recorded retry count
                    retries = llm_retry_count_var.get()

                    # Record output in Langfuse span context
                    if isinstance(result, dict):
                        trace_ctx["output"] = {
                            "routing_destination": result.get("routing_destination"),
                            "has_last_response": bool(result.get("last_response")),
                        }

                    # Log execution to structured logs
                    StructuredLogger.log_agent_execution(
                        agent_name=agent_name,
                        duration=duration,
                        model=model_used,
                        retry_count=retries,
                        errors=None
                    )

                    logger.info(
                        f"===> [SUCCESS] Node: {agent_name} | Duration: {duration:.2f}s | "
                        f"Model: {model_used} | Retries: {retries}"
                    )
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    retries = llm_retry_count_var.get()

                    StructuredLogger.log_agent_execution(
                        agent_name=agent_name,
                        duration=duration,
                        model=model_used,
                        retry_count=retries,
                        errors=str(e)
                    )

                    logger.error(
                        f"===> [EXCEPTION] Node: {agent_name} | Duration: {duration:.2f}s | "
                        f"Error: {str(e)}",
                        exc_info=True
                    )
                    raise e
                finally:
                    # Clean up contextvar
                    llm_retry_count_var.reset(token)
                
        return wrapper
    return decorator
