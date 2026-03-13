"""CDN integration utilities for dashboard exports and static assets.

Provides helpers for CDN-friendly caching and URL generation.
Supports CloudFlare, AWS CloudFront, and custom CDN configurations.
"""

from __future__ import annotations

from typing import Optional

import structlog

from app.config import get_settings

settings = get_settings()
logger = structlog.get_logger()


def get_cdn_url(path: str) -> str:
    """Generate CDN URL for a given path.

    In production with CDN configured, returns CDN URL.
    In development or without CDN, returns direct API URL.

    Args:
        path: Relative path (e.g., "/api/v1/dashboard/123/export/pdf")

    Returns:
        Full URL (CDN or API domain)

    Example:
        >>> get_cdn_url("/api/v1/dashboard/abc/export/pdf")
        "https://cdn.excellentinsight.com/api/v1/dashboard/abc/export/pdf"
    """
    cdn_domain = getattr(settings, "CDN_DOMAIN", None)

    if cdn_domain and settings.APP_ENV == "production":
        return f"https://{cdn_domain}{path}"

    # Fallback to API URL
    # Extract base URL from CORS origins (first origin is usually the production URL)
    if settings.CORS_ORIGINS:
        # Parse domain from CORS origin
        origin = settings.CORS_ORIGINS[0]
        # Remove http:// or https://
        domain = origin.replace("https://", "").replace("http://", "")
        return f"https://{domain}{path}"

    # Ultimate fallback
    return path


def get_cache_control_header(
    cacheable: bool = True,
    max_age: int = 3600,
    immutable: bool = False,
    private: bool = False,
) -> str:
    """Generate Cache-Control header value for different content types.

    Args:
        cacheable: Whether the content can be cached
        max_age: How long to cache (seconds)
        immutable: Whether content never changes (e.g., exports by ID)
        private: Whether cache is user-specific (not shareable)

    Returns:
        Cache-Control header value

    Examples:
        >>> get_cache_control_header(immutable=True, max_age=31536000)
        "public, max-age=31536000, immutable"

        >>> get_cache_control_header(private=True, max_age=60)
        "private, max-age=60"

        >>> get_cache_control_header(cacheable=False)
        "no-store, no-cache, must-revalidate"
    """
    if not cacheable:
        return "no-store, no-cache, must-revalidate"

    parts = []

    # Public vs private
    parts.append("private" if private else "public")

    # Max age
    parts.append(f"max-age={max_age}")

    # Immutable flag (for content that never changes)
    if immutable:
        parts.append("immutable")

    return ", ".join(parts)


def should_use_cdn() -> bool:
    """Check if CDN should be used for current environment.

    Returns:
        True if CDN is configured and enabled
    """
    return (
        settings.APP_ENV == "production"
        and hasattr(settings, "CDN_DOMAIN")
        and settings.CDN_DOMAIN is not None
    )


def get_export_headers(job_id: str, file_format: str, completed_at: Optional[str] = None) -> dict:
    """Generate CDN-optimized headers for dashboard exports.

    Args:
        job_id: Job UUID
        file_format: Export format (pdf, excel, csv)
        completed_at: ISO timestamp of job completion

    Returns:
        Dictionary of HTTP headers for optimal CDN caching

    Features:
        - ETag based on job_id + completion time
        - Immutable cache-control for completed jobs
        - CDN-Cache-Control for CDN-specific rules
        - Vary headers for content negotiation
    """
    import hashlib

    # Generate ETag
    etag_source = f"{job_id}:{completed_at or 'pending'}"
    etag = f'"{hashlib.md5(etag_source.encode()).hexdigest()}"'

    # Completed jobs are immutable (cache forever)
    if completed_at:
        cache_control = get_cache_control_header(
            cacheable=True,
            max_age=31536000,  # 1 year
            immutable=True,
            private=False,
        )
        cdn_cache_control = "public, max-age=31536000, immutable"
    else:
        # Pending/processing jobs shouldn't be cached
        cache_control = get_cache_control_header(cacheable=False)
        cdn_cache_control = "no-store"

    return {
        "Cache-Control": cache_control,
        "CDN-Cache-Control": cdn_cache_control if should_use_cdn() else cache_control,
        "ETag": etag,
        "Vary": "Accept-Encoding",
        "X-Content-Type-Options": "nosniff",
        "X-CDN-Enabled": "true" if should_use_cdn() else "false",
    }


# Predefined cache policies for common content types
CACHE_POLICIES = {
    "dashboard_export": lambda job_id, completed_at: get_export_headers(job_id, "export", completed_at),
    "api_json": lambda: {
        "Cache-Control": get_cache_control_header(private=True, max_age=10),
        "Vary": "Accept-Encoding, Authorization",
    },
    "static_asset": lambda: {
        "Cache-Control": get_cache_control_header(max_age=86400, immutable=True),  # 24 hours
        "Vary": "Accept-Encoding",
    },
}
