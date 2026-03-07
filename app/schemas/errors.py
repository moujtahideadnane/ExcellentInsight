"""Structured error response schemas for the API.

Used in OpenAPI `responses` annotations to document error shapes
consistently across all endpoints.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error envelope returned by all non-2xx responses."""

    detail: str = Field(..., description="Human-readable error description")
    error_code: str = Field(
        default="UNKNOWN_ERROR",
        description="Machine-readable error code (e.g. 'NOT_FOUND', 'VALIDATION_ERROR')",
    )
    request_id: str | None = Field(
        default=None,
        description="Correlation ID for tracing (set by ErrorHandlerMiddleware)",
    )


class ValidationErrorDetail(BaseModel):
    """Single field-level validation error (mirrors FastAPI 422 shape)."""

    loc: list[str | int] = Field(..., description="Path to the invalid field")
    msg: str = Field(..., description="Validation message")
    type: str = Field(..., description="Error type identifier")


class ValidationErrorResponse(BaseModel):
    """Wrapper returned on 422 Unprocessable Entity."""

    detail: list[ValidationErrorDetail]


# ── Reusable response dicts for OpenAPI decorators ────────────────────────────
# Usage:  @router.get("/x", responses={**RESPONSES_401, **RESPONSES_404})

RESPONSES_400: dict[int, dict[str, Any]] = {
    400: {"model": ErrorResponse, "description": "Bad request"},
}

RESPONSES_401: dict[int, dict[str, Any]] = {
    401: {"model": ErrorResponse, "description": "Not authenticated"},
}

RESPONSES_403: dict[int, dict[str, Any]] = {
    403: {"model": ErrorResponse, "description": "Forbidden"},
}

RESPONSES_404: dict[int, dict[str, Any]] = {
    404: {"model": ErrorResponse, "description": "Resource not found"},
}

RESPONSES_409: dict[int, dict[str, Any]] = {
    409: {"model": ErrorResponse, "description": "Conflict / precondition failed"},
}

RESPONSES_413: dict[int, dict[str, Any]] = {
    413: {"model": ErrorResponse, "description": "Payload too large"},
}

RESPONSES_422: dict[int, dict[str, Any]] = {
    422: {"model": ValidationErrorResponse, "description": "Validation error"},
}

RESPONSES_500: dict[int, dict[str, Any]] = {
    500: {"model": ErrorResponse, "description": "Internal server error"},
}
