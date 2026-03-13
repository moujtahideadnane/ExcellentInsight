"""Response compression middleware for gzip and brotli.

Automatically compresses responses based on Accept-Encoding header.
Brotli is preferred (better compression) when supported by client.
"""

import gzip
import io
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = structlog.get_logger()

# Minimum response size to compress (bytes)
# Responses smaller than this aren't worth compressing (overhead > benefit)
MIN_COMPRESSION_SIZE = 500

# Content types that benefit from compression
COMPRESSIBLE_TYPES = {
    "application/json",
    "application/javascript",
    "application/xml",
    "text/html",
    "text/css",
    "text/plain",
    "text/xml",
    "text/csv",
    "image/svg+xml",
}


class CompressionMiddleware(BaseHTTPMiddleware):
    """Middleware to compress responses using gzip or brotli.

    Features:
    - Automatic algorithm selection based on Accept-Encoding
    - Brotli preferred (better compression ratio)
    - Skip compression for small responses or incompatible content types
    - Skip compression if already compressed (Content-Encoding present)
    """

    def __init__(self, app: ASGIApp, min_size: int = MIN_COMPRESSION_SIZE):
        super().__init__(app)
        self.min_size = min_size

        # Try to import brotli (optional dependency)
        try:
            import brotli

            self.brotli = brotli
            self.has_brotli = True
        except ImportError:
            self.brotli = None
            self.has_brotli = False
            logger.info("compression_middleware_no_brotli", msg="Brotli not available, using gzip only")

    def should_compress(self, response: Response) -> bool:
        """Determine if response should be compressed."""
        # Skip if already compressed
        if "content-encoding" in response.headers:
            return False

        # Skip if content-length is too small
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) < self.min_size:
            return False

        # Check content type
        content_type = response.headers.get("content-type", "")
        content_type_base = content_type.split(";")[0].strip()

        return content_type_base in COMPRESSIBLE_TYPES

    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)

        # Skip compression for SSE (text/event-stream)
        if response.headers.get("content-type", "").startswith("text/event-stream"):
            return response

        # Skip if response doesn't qualify for compression
        if not self.should_compress(response):
            return response

        # Get client's accepted encodings
        accept_encoding = request.headers.get("accept-encoding", "").lower()

        # Read response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        # Skip if body is too small
        if len(body) < self.min_size:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        # Compress with brotli (preferred) or gzip
        compressed_body = None
        encoding = None

        if self.has_brotli and "br" in accept_encoding:
            # Brotli compression (quality 4 = fast, quality 11 = best)
            compressed_body = self.brotli.compress(body, quality=4)
            encoding = "br"
        elif "gzip" in accept_encoding:
            # Gzip compression (level 6 = balanced)
            buffer = io.BytesIO()
            with gzip.GzipFile(fileobj=buffer, mode="wb", compresslevel=6) as gzip_file:
                gzip_file.write(body)
            compressed_body = buffer.getvalue()
            encoding = "gzip"

        # Only use compression if it actually reduces size
        if compressed_body and len(compressed_body) < len(body):
            headers = dict(response.headers)
            headers["content-encoding"] = encoding
            headers["content-length"] = str(len(compressed_body))

            # Add Vary header to indicate response varies by Accept-Encoding
            vary = headers.get("vary", "")
            if vary:
                headers["vary"] = f"{vary}, Accept-Encoding"
            else:
                headers["vary"] = "Accept-Encoding"

            logger.debug(
                "response_compressed",
                encoding=encoding,
                original_size=len(body),
                compressed_size=len(compressed_body),
                ratio=f"{len(compressed_body) / len(body) * 100:.1f}%",
            )

            return Response(
                content=compressed_body,
                status_code=response.status_code,
                headers=headers,
                media_type=response.media_type,
            )

        # Compression didn't help, return original
        return Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
