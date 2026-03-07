import uuid

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Prefer request.state.request_id if set by RequestIDMiddleware
        request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())[:8]
        structlog.contextvars.bind_contextvars(request_id=request_id)

        try:
            response = await call_next(request)
            # Ensure every response has the request id header
            response.headers.setdefault("X-Request-ID", request_id)
            return response
        except Exception as exc:
            # Log the exception with structured context and return standardized error envelope
            logger.exception("Unhandled error", path=str(request.url.path), error=str(exc))
            payload = {
                "detail": "Internal server error",
                "error_code": "INTERNAL_ERROR",
                "request_id": request_id,
            }
            return JSONResponse(
                status_code=500,
                content=payload,
                headers={"X-Request-ID": request_id},
            )
