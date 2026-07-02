import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import request_id_var, logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        token = request_id_var.set(request_id)

        start_time = time.time()
        logger.info(f"Incoming request: {request.method} {request.url.path}")

        try:
            response = await call_next(request)
            duration = time.time() - start_time
            response.headers["X-Request-ID"] = request_id
            logger.info(
                f"Completed request: {request.method} {request.url.path} - Status {response.status_code} (Duration: {duration:.4f}s)"
            )
            return response
        except Exception as e:
            duration = time.time() - start_time
            logger.exception(
                f"Request failed: {request.method} {request.url.path} - {str(e)} (Duration: {duration:.4f}s)"
            )
            raise e
        finally:
            request_id_var.reset(token)
