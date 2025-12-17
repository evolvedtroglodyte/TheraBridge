"""
Rate limiting middleware using slowapi.

Provides configurable rate limits to prevent abuse and ensure fair resource usage.
Default: 100 requests per minute per IP address.
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

# Initialize limiter with default rate limit
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"]
)


def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors.

    Returns a structured JSON response with retry information.

    Args:
        request: FastAPI request object
        exc: Rate limit exception with retry_after info

    Returns:
        JSONResponse with 429 status and retry headers
    """
    return JSONResponse(
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": exc.retry_after
        },
        status_code=429,
        headers={"Retry-After": str(exc.retry_after)}
    )


__all__ = ['limiter', 'custom_rate_limit_handler']
