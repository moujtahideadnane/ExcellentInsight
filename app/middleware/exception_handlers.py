from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    error_code = None
    # Try to read a custom error code passed via headers on the exception
    if exc.headers and "X-Error-Code" in exc.headers:
        error_code = exc.headers.get("X-Error-Code")
    payload: dict[str, Any] = {
        "detail": detail,
        "error_code": error_code or f"HTTP_{exc.status_code}",
        "request_id": request_id,
    }
    return JSONResponse(status_code=exc.status_code, content=payload)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    import structlog
    logger = structlog.get_logger()

    request_id = getattr(request.state, "request_id", None)

    # Log detailed validation errors for debugging
    logger.error(
        "validation_error",
        request_id=request_id,
        errors=exc.errors(),
        body=exc.body if hasattr(exc, 'body') else None,
    )

    payload = {
        "detail": "Validation error",
        "error_code": "VALIDATION_ERROR",
        "request_id": request_id,
        "errors": exc.errors(),  # Include actual validation errors in response
    }
    return JSONResponse(status_code=422, content=payload)
