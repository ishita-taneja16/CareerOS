import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from core.logging_manager import StructuredLogger

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        """Intercepts HTTP calls to track timing, status codes, and errors."""
        start_time = time.time()
        error_message = None
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as e:
            error_message = str(e)
            raise e
        finally:
            duration = time.time() - start_time
            StructuredLogger.log_api_request(
                endpoint=request.url.path,
                execution_time=duration,
                status_code=status_code,
                errors=error_message
            )
