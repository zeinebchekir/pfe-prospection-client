"""
Cookie utility helpers for JWT token delivery.

Tokens are stored in HTTP-only cookies to prevent XSS attacks.
JavaScript cannot read these cookies (httpOnly=True),
while they are still sent automatically by the browser on every request.
"""
from django.conf import settings


def set_auth_cookies(response, access_token: str, refresh_token: str | None = None) -> None:
    """
    Attach JWT tokens as HTTP-only cookies to the response.

    Args:
        response: DRF Response object.
        access_token: Short-lived access JWT string.
        refresh_token: Long-lived refresh JWT string (optional on pure refresh calls).
    """
    cookie_kwargs = {
        "httponly": settings.AUTH_COOKIE_HTTP_ONLY,
        "secure": settings.AUTH_COOKIE_SECURE,
        "samesite": settings.AUTH_COOKIE_SAMESITE,
        "path": "/",
    }
    if settings.AUTH_COOKIE_DOMAIN:
        cookie_kwargs["domain"] = settings.AUTH_COOKIE_DOMAIN

    response.set_cookie(
        key=settings.AUTH_COOKIE_ACCESS,
        value=access_token,
        max_age=settings.AUTH_COOKIE_ACCESS_MAX_AGE,
        **cookie_kwargs,
    )

    if refresh_token is not None:
        response.set_cookie(
            key=settings.AUTH_COOKIE_REFRESH,
            value=refresh_token,
            max_age=settings.AUTH_COOKIE_REFRESH_MAX_AGE,
            **cookie_kwargs,
        )


def unset_auth_cookies(response) -> None:
    """
    Delete JWT cookies by setting them to empty strings with max_age=0.
    """
    delete_kwargs = {
        "path": "/",
        "samesite": settings.AUTH_COOKIE_SAMESITE,
    }
    if settings.AUTH_COOKIE_SECURE:
        delete_kwargs["secure"] = True
    if settings.AUTH_COOKIE_DOMAIN:
        delete_kwargs["domain"] = settings.AUTH_COOKIE_DOMAIN

    response.delete_cookie(settings.AUTH_COOKIE_ACCESS, **delete_kwargs)
    response.delete_cookie(settings.AUTH_COOKIE_REFRESH, **delete_kwargs)
