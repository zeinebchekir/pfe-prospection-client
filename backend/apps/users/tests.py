"""
Tests for the auth API endpoints.

Tests cover: register, login, logout, refresh, and profile (me) endpoints.
Each test class is self-contained with its own user setup.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

REGISTER_URL = reverse("users:register")
LOGIN_URL = reverse("users:login")
LOGOUT_URL = reverse("users:logout")
REFRESH_URL = reverse("users:refresh")
ME_URL = reverse("users:me")

VALID_PAYLOAD = {
    "email": "test@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
}


def create_user(**kwargs) -> User:
    defaults = {"email": "user@example.com", "password": "SecurePass123!"}
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


def auth_client_for(user) -> APIClient:
    """Returns an APIClient with valid JWT cookies for the given user."""
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.cookies["access_token"] = str(refresh.access_token)
    client.cookies["refresh_token"] = str(refresh)
    return client


class TestRegister(TestCase):
    """POST /api/auth/register/"""

    def setUp(self):
        self.client = APIClient()

    def test_register_success_returns_201_and_sets_cookies(self):
        res = self.client.post(REGISTER_URL, VALID_PAYLOAD, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", res.data)
        self.assertEqual(res.data["user"]["email"], VALID_PAYLOAD["email"])
        # Cookies must be set
        self.assertIn("access_token", res.cookies)
        self.assertIn("refresh_token", res.cookies)
        # Cookies must be HttpOnly
        self.assertTrue(res.cookies["access_token"]["httponly"])
        self.assertTrue(res.cookies["refresh_token"]["httponly"])

    def test_register_duplicate_email_returns_400(self):
        create_user(email=VALID_PAYLOAD["email"])
        res = self.client.post(REGISTER_URL, VALID_PAYLOAD, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_mismatch_returns_400(self):
        payload = {**VALID_PAYLOAD, "password2": "DifferentPassword!"}
        res = self.client.post(REGISTER_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_weak_password_returns_400(self):
        payload = {**VALID_PAYLOAD, "password": "123", "password2": "123"}
        res = self.client.post(REGISTER_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_email_returns_400(self):
        payload = {"password": "SecurePass123!", "password2": "SecurePass123!"}
        res = self.client.post(REGISTER_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class TestLogin(TestCase):
    """POST /api/auth/login/"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()

    def test_login_valid_credentials_returns_200_and_cookies(self):
        res = self.client.post(LOGIN_URL, {
            "email": "user@example.com",
            "password": "SecurePass123!",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", res.cookies)
        self.assertIn("refresh_token", res.cookies)
        self.assertTrue(res.cookies["access_token"]["httponly"])

    def test_login_wrong_password_returns_401(self):
        res = self.client.post(LOGIN_URL, {
            "email": "user@example.com",
            "password": "WrongPassword!",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access_token", res.cookies)

    def test_login_nonexistent_email_returns_401(self):
        res = self.client.post(LOGIN_URL, {
            "email": "nobody@example.com",
            "password": "SecurePass123!",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_inactive_user_returns_403(self):
        self.user.is_active = False
        self.user.save()
        res = self.client.post(LOGIN_URL, {
            "email": "user@example.com",
            "password": "SecurePass123!",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class TestLogout(TestCase):
    """POST /api/auth/logout/"""

    def setUp(self):
        self.user = create_user()
        self.client = auth_client_for(self.user)

    def test_logout_authenticated_user_returns_200_and_clears_cookies(self):
        res = self.client.post(LOGOUT_URL, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Cookies should be deleted (max-age=0 or empty value)
        self.assertEqual(res.cookies.get("access_token", None) and
                         res.cookies["access_token"].value, "")

    def test_logout_unauthenticated_returns_401(self):
        client = APIClient()
        res = client.post(LOGOUT_URL, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class TestRefresh(TestCase):
    """POST /api/auth/refresh/"""

    def setUp(self):
        self.user = create_user()
        self.client = auth_client_for(self.user)

    def test_refresh_with_valid_cookie_returns_200_and_new_cookies(self):
        res = self.client.post(REFRESH_URL, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", res.cookies)

    def test_refresh_without_cookie_returns_401(self):
        client = APIClient()
        res = client.post(REFRESH_URL, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_with_invalid_token_returns_401(self):
        client = APIClient()
        client.cookies["refresh_token"] = "not.a.real.token"
        res = client.post(REFRESH_URL, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class TestMe(TestCase):
    """GET /api/auth/me/"""

    def setUp(self):
        self.user = create_user(email="profile@example.com", first_name="John", last_name="Doe")
        self.client = auth_client_for(self.user)

    def test_me_with_valid_cookie_returns_user_profile(self):
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["user"]["email"], "profile@example.com")
        self.assertEqual(res.data["user"]["first_name"], "John")
        # Password must NOT be in response
        self.assertNotIn("password", res.data["user"])

    def test_me_without_cookie_returns_401(self):
        client = APIClient()
        res = client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_response_does_not_contain_password(self):
        res = self.client.get(ME_URL)
        self.assertNotIn("password", str(res.data))
