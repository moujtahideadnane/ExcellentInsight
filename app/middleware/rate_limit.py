from typing import Optional

import redis.asyncio as redis
import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings

settings = get_settings()
logger = structlog.get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_url: str = None):
        super().__init__(app)
        self.redis_url = redis_url or settings.REDIS_URL
        self._redis = None

        # Rate limits (authenticated, by org)
        self.general_limit = 30    # requests per minute
        self.upload_limit = 10     # uploads per hour
        self.general_window = 60   # seconds
        self.upload_window = 3600  # seconds

        # Rate limits (unauthenticated auth endpoints, by IP) — brute-force guard
        self.auth_limit = 20   # attempts per 15 minutes
        self.auth_window = 900  # 15 minutes

    async def _get_redis(self):
        if self._redis is None:
            self._redis = redis.from_url(self.redis_url)
        return self._redis

    async def _get_org_id_from_token(self, request: Request) -> Optional[str]:
        """Extract org_id from JWT token in Authorization header and honor blocklist."""
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]

        try:
            # Check Redis blocklist: if token is revoked, treat as no org_id.
            r = await self._get_redis()
            is_blocked = await r.get(f"blocklist:{token}")
            if is_blocked:
                return None
        except Exception:
            # On Redis failure, fall back to decoding the token without blocklist enforcement here.
            pass

        try:
            from app.utils.security import decode_token

            payload = decode_token(token)
            return payload.get("org_id")
        except Exception:
            return None

    def _get_client_ip(self, request: Request) -> str:
        """Extract the real client IP, respecting X-Forwarded-For from a trusted proxy."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can be a comma-separated list; the first entry is the client IP
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def _check_rate_limit(self, org_id: str, endpoint: str, limit: int, window: int) -> tuple[bool, int]:
        """Check if request is within rate limit. Returns (allowed, retry_after)."""
        try:
            r = await self._get_redis()
            key = f"ratelimit:{org_id}:{endpoint}:{window}"

            # Atomic INCR avoids the GET → INCR race condition
            current = await r.incr(key)
            if current == 1:
                # First request in this window — set the expiry
                await r.expire(key, window)

            if current > limit:
                ttl = await r.ttl(key)
                return False, max(ttl, 0)

            return True, 0
        except Exception as e:
            # If Redis fails, allow the request (fail open)
            logger.error("Rate limit check failed", error=str(e))
            return True, 0

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Health check is always free — never rate-limited
        if path == "/health":
            return await call_next(request)

        # Auth endpoints: IP-based rate limiting to prevent brute-force attacks.
        # These used to be whitelisted entirely, which allowed unlimited login attempts.
        auth_routes = ["/api/v1/auth/login", "/api/v1/auth/signup", "/api/v1/auth/refresh"]
        if any(path.startswith(route) for route in auth_routes):
            client_ip = self._get_client_ip(request)
            allowed, retry_after = await self._check_rate_limit(
                f"ip:{client_ip}", "auth", self.auth_limit, self.auth_window
            )
            if not allowed:
                logger.warning("Auth rate limit exceeded", ip=client_ip, path=path)
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many attempts. Please try again later.", "retry_after": retry_after},
                    headers={"Retry-After": str(retry_after)},
                )
            return await call_next(request)

        # For all other routes: require a token for org-based rate limiting
        org_id = await self._get_org_id_from_token(request)
        if not org_id:
            # No valid token — the auth middleware will handle the 401
            return await call_next(request)

        # Determine rate limit tier based on endpoint
        is_upload = path.endswith("/upload") or "/upload" in path

        if is_upload:
            allowed, retry_after = await self._check_rate_limit(org_id, "upload", self.upload_limit, self.upload_window)
        else:
            allowed, retry_after = await self._check_rate_limit(
                org_id, "general", self.general_limit, self.general_window
            )

        if not allowed:
            logger.warning("Rate limit exceeded", org_id=org_id, path=path)
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later.", "retry_after": retry_after},
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
