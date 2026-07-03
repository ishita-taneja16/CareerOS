import os
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")

class StructuredLogger:
    @staticmethod
    def _write_log(file_name: str, data: Dict[str, Any]) -> None:
        """Appends a structured JSON log line to the specified log file."""
        try:
            if not os.path.exists(LOGS_DIR):
                os.makedirs(LOGS_DIR, exist_ok=True)
            
            log_path = os.path.join(LOGS_DIR, file_name)
            # Add ISO timestamp to every logged record
            data["timestamp"] = datetime.utcnow().isoformat()
            
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(data) + "\n")
        except Exception as e:
            # Fallback to standard print to avoid crash loop
            print(f"Failed to write structured log to {file_name}: {str(e)}")

    @classmethod
    def log_api_request(
        cls,
        endpoint: str,
        execution_time: float,
        status_code: int,
        errors: Optional[str] = None
    ) -> None:
        """Logs structured API HTTP requests."""
        cls._write_log("api_requests.jsonl", {
            "endpoint": endpoint,
            "execution_time_seconds": round(execution_time, 4),
            "status_code": status_code,
            "errors": errors
        })

    @classmethod
    def log_agent_execution(
        cls,
        agent_name: str,
        duration: float,
        model: str,
        retry_count: int,
        errors: Optional[str] = None
    ) -> None:
        """Logs structured LangGraph node executions."""
        cls._write_log("agent_executions.jsonl", {
            "agent_name": agent_name,
            "execution_duration_seconds": round(duration, 4),
            "llm_model": model,
            "retry_count": retry_count,
            "errors": errors
        })
