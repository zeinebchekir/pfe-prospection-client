"""
Custom JWT authentication that reads the access token from HTTP-only cookies
instead of the Authorization header.

This prevents token leakage via XSS — JavaScript can never access the token.
"""
import logging
from typing import Optional, Tuple

from django.conf import settings
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

logger = logging.getLogger(__name__)


class CookieJWTAuthentication(JWTAuthentication):
    """
    Authenticates requests by reading the access JWT from an HTTP-only cookie.

    Falls back gracefully to None (anonymous) if the cookie is absent or invalid,
    which lets the permission layer produce the correct 401/403 response.
    """

    def authenticate(self, request: Request) -> Optional[Tuple]:
        access_cookie = request.COOKIES.get(settings.AUTH_COOKIE_ACCESS)

        if not access_cookie:
            return None  # No cookie present → anonymous request

        try:
            validated_token = self.get_validated_token(access_cookie)
            user = self.get_user(validated_token)
            return user, validated_token
        except (InvalidToken, TokenError) as exc:
            logger.debug("Cookie JWT authentication failed: %s", exc)
            return None  # Invalid/expired token → let permission deny access
