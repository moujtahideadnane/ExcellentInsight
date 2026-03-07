import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Reuse incoming header if present to allow correlation from upstream
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        # Expose on request state for handlers and other middleware
        request.state.request_id = request_id
        response = await call_next(request)
        # Ensure response contains the header
        response.headers.setdefault("X-Request-ID", request_id)
        return response
