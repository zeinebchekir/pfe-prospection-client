"""
Auth API views.

All endpoints use HTTP-only cookie-based JWT tokens — no Authorization header.

Endpoints:
  POST /api/auth/register/   → Create account, set cookies, return user data
  POST /api/auth/login/      → Validate credentials, set cookies, return user data
  POST /api/auth/logout/     → Blacklist refresh token, clear cookies
  POST /api/auth/refresh/    → Issue new access + rotated refresh token in cookies
  GET  /api/auth/me/         → Return authenticated user profile
  PATCH /api/auth/me/        → Update own profile (nom, prenom, fonction)

Swagger/OpenAPI metadata is added via @extend_schema decorators from drf-spectacular.
No behavior is affected by these decorators.
"""
import logging
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import (
    extend_schema, extend_schema_view,
    OpenApiResponse, OpenApiExample, OpenApiParameter,
    inline_serializer,
)
from drf_spectacular.types import OpenApiTypes

from .models import PasswordResetToken
from .serializers import (
    LoginSerializer, RegisterSerializer, UserProfileSerializer,
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    ProfileUpdateSerializer, ChangePasswordSerializer
)
from .utils import set_auth_cookies, unset_auth_cookies
from .permissions import IsAdmin
from apps.audit.utils import log_action
from apps.audit.models import AuditLog

User = get_user_model()
logger = logging.getLogger(__name__)


def get_client_ip(request):
    """
    Extract the real client IP address from the request.

    Checks X-Forwarded-For first (set by reverse proxies / load balancers)
    and falls back to REMOTE_ADDR for direct connections.
    Used to populate the ip_address field in audit log entries.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]  # Take the leftmost (original client) IP
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@extend_schema(
    tags=["Authentication"],
    summary="Register a new user account",
    description=(
        "Creates a new user account with role **COMMERCIAL** (fixed — cannot be overridden at registration). "
        "On success the user is immediately authenticated: two HTTP-only cookies are set on the response.\n\n"
        "**Cookie behavior (not visible in Swagger):**\n"
        "- `access_token` — HttpOnly, 10 min, used for API authentication\n"
        "- `refresh_token` — HttpOnly, 7 days, used to silently rotate the access token\n\n"
        "No email confirmation step is required."
    ),
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(
            response=UserProfileSerializer,
            description="Account created. Auth cookies set. User profile returned.",
            examples=[
                OpenApiExample(
                    "Successful registration",
                    value={"status": "success", "user": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "email": "jean@example.com",
                        "nom": "Dupont",
                        "prenom": "Jean",
                        "role": "COMMERCIAL",
                        "full_name": "Jean Dupont",
                        "fonction": ""
                    }},
                    response_only=True,
                )
            ]
        ),
        400: OpenApiResponse(
            description="Validation error: duplicate email, password mismatch, or weak password.",
            examples=[
                OpenApiExample(
                    "Duplicate email",
                    value={"status": "error", "code": 400, "errors": {"email": ["user with this email already exists."]}},
                    response_only=True,
                ),
                OpenApiExample(
                    "Password mismatch",
                    value={"status": "error", "code": 400, "errors": {"password": ["Les mots de passe ne correspondent pas."]}},
                    response_only=True,
                ),
            ]
        ),
    },
    auth=[],  # Public endpoint — no auth cookie needed
)
class RegisterView(APIView):
    """
    POST /api/auth/register/

    Open endpoint: creates a new user account with role=COMMERCIAL (fixed),
    issues JWT tokens, and sets them as HTTP-only cookies on the response.

    After successful registration the user is immediately authenticated
    (no email confirmation step).
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # Disable auth check — registration is always open

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()  # Calls User.objects.create_user() — hashes password

        # Issue a JWT pair immediately so the user is logged in after registration
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        user_data = UserProfileSerializer(user).data
        response = Response(
            {"status": "success", "user": user_data},
            status=status.HTTP_201_CREATED,
        )
        # Store tokens as HTTP-only cookies — JavaScript cannot read these
        set_auth_cookies(response, access_token=access, refresh_token=str(refresh))
        logger.info("New user registered: %s", user.email)
        return response


@extend_schema(
    tags=["Authentication"],
    summary="Authenticate user (login)",
    description=(
        "Validates email and password against the database. On success, sets two HTTP-only JWT cookies.\n\n"
        "**Tokens are never returned in the JSON body** — they are stored exclusively in browser cookies.\n\n"
        "**Cookie behavior:**\n"
        "- `access_token` — HttpOnly, 10 min\n"
        "- `refresh_token` — HttpOnly, 7 days\n\n"
        "**Error distinctions:**\n"
        "- `401` — wrong email or password\n"
        "- `403` with `code: ACCOUNT_INACTIVE` — account disabled by admin\n\n"
        "A `LOGIN` event is written to the audit log on success."
    ),
    request=LoginSerializer,
    responses={
        200: OpenApiResponse(
            response=UserProfileSerializer,
            description="Login successful. Auth cookies set.",
            examples=[
                OpenApiExample(
                    "Successful login",
                    value={"status": "success", "user": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "email": "jean@example.com",
                        "nom": "Dupont",
                        "prenom": "Jean",
                        "role": "COMMERCIAL",
                        "full_name": "Jean Dupont",
                        "fonction": ""
                    }},
                    response_only=True,
                )
            ]
        ),
        401: OpenApiResponse(
            description="Invalid email or password.",
            examples=[
                OpenApiExample(
                    "Wrong credentials",
                    value={"status": "error", "message": "Email ou mot de passe invalide."},
                    response_only=True,
                )
            ]
        ),
        403: OpenApiResponse(
            description="Account is inactive. Contact the administrator.",
            examples=[
                OpenApiExample(
                    "Inactive account",
                    value={"status": "error", "message": "Votre accès est bloqué. Veuillez contacter l'administrateur.", "code": "ACCOUNT_INACTIVE"},
                    response_only=True,
                )
            ]
        ),
    },
    auth=[],  # Public endpoint
)
class LoginView(APIView):
    """
    POST /api/auth/login/

    Validates credentials, issues JWT tokens, and sets HTTP-only cookies.
    Distinguishes between wrong credentials (401) and inactive accounts (403)
    to give actionable feedback without revealing which emails are registered.

    Writes a LOGIN entry to the audit log on success.
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # No auth needed to log in

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = authenticate(request, email=email, password=password)

        if user is None:
            # Check if user exists but is inactive
            user_exists = User.objects.filter(email=email).first()
            if user_exists and not user_exists.is_active:
                return Response(
                    {
                        "status": "error", 
                        "message": "Votre accès est bloqué. Veuillez contacter l'administrateur.",
                        "code": "ACCOUNT_INACTIVE"
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
            
            return Response(
                {"status": "error", "message": "Email ou mot de passe invalide."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # This block is now redundant because authenticate() only returns active users by default,
        # and we handled the inactive case above.
        if not user.is_active:
            return Response(
                {
                    "status": "error", 
                    "message": "Votre accès est bloqué. Veuillez contacter l'administrateur.",
                    "code": "ACCOUNT_INACTIVE"
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        user_data = UserProfileSerializer(user).data
        response = Response(
            {"status": "success", "user": user_data},
            status=status.HTTP_200_OK,
        )
        set_auth_cookies(response, access_token=access, refresh_token=str(refresh))
        
        log_action(user, AuditLog.Action.LOGIN, user.email, get_client_ip(request))
        logger.info("User logged in: %s", user.email)
        return response


@extend_schema(
    tags=["Authentication"],
    summary="Logout (invalidate session)",
    description=(
        "Blacklists the current `refresh_token` cookie so it cannot be reused, "
        "then deletes both auth cookies from the browser.\n\n"
        "**Important:** The `access_token` (10-minute lifetime) is not explicitly revoked — "
        "it expires naturally. Cookie deletion prevents it from being sent on further requests.\n\n"
        "**Requires:** Valid `access_token` cookie.\n\n"
        "A `LOGOUT` event is written to the audit log."
    ),
    request=None,
    responses={
        200: OpenApiResponse(
            description="Logout successful. Auth cookies cleared.",
            examples=[
                OpenApiExample(
                    "Logged out",
                    value={"status": "success", "message": "Déconnexion réussie."},
                    response_only=True,
                )
            ]
        ),
        401: OpenApiResponse(description="Missing or expired access_token cookie."),
    },
)
class LogoutView(APIView):
    """
    POST /api/auth/logout/

    Blacklists the refresh token so it cannot be reused, then clears
    both auth cookies from the browser.

    The access token (10-minute lifetime) is not explicitly revoked — it
    will expire naturally. The cookie deletion prevents the browser from
    sending it further, which is sufficient for normal usage.

    Writes a LOGOUT entry to the audit log.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Read the refresh token before clearing cookies
        refresh_token = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH)

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                # Blacklisting adds the token's JTI to the OutstandingToken/BlacklistedToken tables.
                # After this, presenting this refresh token will return 401.
                token.blacklist()
            except Exception:
                # If the token is already invalid/expired, silently continue.
                # The important part is clearing the cookies.
                pass

        response = Response(
            {"status": "success", "message": "Déconnexion réussie."},
            status=status.HTTP_200_OK,
        )
        unset_auth_cookies(response)  # Delete both access_token and refresh_token cookies
        log_action(request.user, AuditLog.Action.LOGOUT, request.user.email, get_client_ip(request))
        logger.info("User logged out: %s", request.user.email)
        return response


@extend_schema(
    tags=["Authentication"],
    summary="Refresh access token",
    description=(
        "Reads the `refresh_token` from its HTTP-only cookie, validates it, and issues a "
        "new access + refresh token pair (token rotation).\n\n"
        "**The old refresh token is immediately blacklisted** — it cannot be reused.\n\n"
        "**No request body is needed.** The browser sends the `refresh_token` cookie automatically.\n\n"
        "**Note:** This endpoint is called automatically by the Axios interceptor when any API "
        "call returns 401 (access token expired). The user sees no interruption.\n\n"
        "**Concurrent requests during refresh** are queued in `pendingRequests[]` and replayed "
        "after the new tokens are set — only one refresh call is made regardless of how many "
        "requests were pending."
    ),
    request=None,
    responses={
        200: OpenApiResponse(
            description="Tokens rotated. New auth cookies set.",
            examples=[
                OpenApiExample(
                    "Refresh successful",
                    value={"status": "success", "message": "Token refreshed."},
                    response_only=True,
                )
            ]
        ),
        401: OpenApiResponse(
            description="No refresh token cookie, or token is expired / blacklisted.",
            examples=[
                OpenApiExample(
                    "No cookie",
                    value={"status": "error", "message": "No refresh token provided."},
                    response_only=True,
                ),
                OpenApiExample(
                    "Invalid token",
                    value={"status": "error", "message": "Token is invalid or expired."},
                    response_only=True,
                ),
            ]
        ),
    },
    auth=[],  # Uses refresh_token cookie, not access_token
)
class RefreshView(APIView):
    """
    POST /api/auth/refresh/

    Reads the refresh token from its HTTP-only cookie, validates it,
    and issues a new access + refresh token pair (token rotation).

    The old refresh token is immediately blacklisted (BLACKLIST_AFTER_ROTATION=True).
    New tokens are set as HTTP-only cookies — the response body contains no token values.

    This endpoint is called automatically by the Axios interceptor on 401 responses,
    making token refresh transparent to the user.
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # No access token needed — only the refresh cookie

    def post(self, request):
        refresh_token = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH)

        if not refresh_token:
            return Response(
                {"status": "error", "message": "No refresh token provided."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            refresh = RefreshToken(refresh_token)
            new_access = str(refresh.access_token)
            new_refresh = str(refresh)

            response = Response(
                {"status": "success", "message": "Token refreshed."},
                status=status.HTTP_200_OK,
            )
            set_auth_cookies(response, access_token=new_access, refresh_token=new_refresh)
            return response

        except TokenError as exc:
            logger.warning("Token refresh failed: %s", exc)
            return Response(
                {"status": "error", "message": "Token is invalid or expired."},
                status=status.HTTP_401_UNAUTHORIZED,
            )


@extend_schema_view(
    get=extend_schema(
        tags=["Current User"],
        summary="Get authenticated user profile",
        description=(
            "Returns the profile of the currently authenticated user.\n\n"
            "This endpoint is called on every page load by the Vue Router guard (`fetchUser()`) "
            "to restore session state from the HTTP-only cookie. No token value is ever stored "
            "in localStorage or sessionStorage.\n\n"
            "**Password is never included in the response.**"
        ),
        responses={
            200: OpenApiResponse(
                response=UserProfileSerializer,
                description="Authenticated user profile.",
                examples=[
                    OpenApiExample(
                        "User profile",
                        value={"status": "success", "user": {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "email": "jean@example.com",
                            "nom": "Dupont",
                            "prenom": "Jean",
                            "role": "COMMERCIAL",
                            "full_name": "Jean Dupont",
                            "fonction": "Account Manager"
                        }},
                        response_only=True,
                    )
                ]
            ),
            401: OpenApiResponse(description="Missing or expired access_token cookie."),
        },
    ),
    patch=extend_schema(
        tags=["Current User"],
        summary="Update own profile",
        description=(
            "Updates the authenticated user's own profile fields.\n\n"
            "**Editable fields:** `nom`, `prenom`, `fonction`\n\n"
            "**Not editable via this endpoint:** `email`, `role`, `is_active`\n\n"
            "Requires `X-CSRFToken` header (provided automatically by the Axios interceptor)."
        ),
        request=ProfileUpdateSerializer,
        responses={
            200: OpenApiResponse(
                response=UserProfileSerializer,
                description="Profile updated successfully.",
            ),
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(description="Not authenticated."),
        },
    ),
)
class MeView(APIView):
    """
    GET /api/auth/me/    — Return authenticated user profile
    PATCH /api/auth/me/  — Update own profile (name and fonction only)

    This endpoint is called on every page load by the router guard (fetchUser())
    to restore session state from the HTTP-only cookie without storing
    any auth data in localStorage or sessionStorage.

    Note: Users cannot change their own role or email via this endpoint.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(
            {"status": "success", "user": serializer.data},
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        log_action(
            user, 
            AuditLog.Action.UPDATE, 
            user.email, 
            get_client_ip(request), 
            {'action': 'profile_update'}
        )
        
        return Response({
            "status": "success", 
            "user": UserProfileSerializer(user).data
        })


@extend_schema(
    tags=["Current User"],
    summary="Change own password",
    description=(
        "Allows the authenticated user to change their own password. "
        "The current password must be provided for verification.\n\n"
        "**Note:** Changing the password does **not** invalidate existing JWT sessions. "
        "If the account is believed to be compromised, an admin should also deactivate "
        "the account via `toggle-active/`."
    ),
    request=ChangePasswordSerializer,
    responses={
        200: OpenApiResponse(
            description="Password updated successfully.",
            examples=[
                OpenApiExample(
                    "Success",
                    value={"status": "success", "message": "Mot de passe mis à jour avec succès."},
                    response_only=True,
                )
            ]
        ),
        400: OpenApiResponse(
            description="Old password incorrect, passwords don't match, or new password too weak.",
            examples=[
                OpenApiExample(
                    "Wrong old password",
                    value={"error": "Le mot de passe actuel est incorrect."},
                    response_only=True,
                )
            ]
        ),
        401: OpenApiResponse(description="Not authenticated."),
    },
)
class ChangePasswordView(APIView):
    """
    POST /api/auth/change-password/

    Allows an authenticated user to change their own password.
    Requires verification of the current password before accepting a new one.

    Note: This does NOT invalidate existing sessions or JWT tokens.
    A compromised account should also have the admin deactivate it via toggle-active.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {"error": "Le mot de passe actuel est incorrect."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        log_action(
            user, 
            AuditLog.Action.UPDATE, 
            user.email, 
            get_client_ip(request), 
            {'action': 'password_change'}
        )
        
        return Response({"status": "success", "message": "Mot de passe mis à jour avec succès."})


# ── Vues d'administration des utilisateurs ────────────────────────────────

@extend_schema_view(
    list=extend_schema(
        tags=["Admin Users"],
        summary="List all non-admin users",
        description=(
            "Returns a paginated list of all users with role `CEO` or `COMMERCIAL`.\n\n"
            "**ADMIN role required.**\n\n"
            "**Filters available:**\n"
            "- `role` — filter by role value (`CEO`, `COMMERCIAL`)\n"
            "- `is_active` — filter by active status (`true` / `false`)\n"
            "- `search` — search by nom, prenom, or email (case-insensitive)"
        ),
        parameters=[
            OpenApiParameter("role", OpenApiTypes.STR, description="Filter by role: CEO or COMMERCIAL"),
            OpenApiParameter("is_active", OpenApiTypes.STR, description="Filter by active status: true or false"),
            OpenApiParameter("search", OpenApiTypes.STR, description="Search by nom, prenom, or email"),
        ],
        responses={200: UserSerializer(many=True)},
    ),
    create=extend_schema(
        tags=["Admin Users"],
        summary="Create a user (admin-only)",
        description=(
            "Creates a new user with any role (ADMIN can assign CEO, COMMERCIAL, or ADMIN).\n\n"
            "**ADMIN role required.**\n\n"
            "Unlike self-registration (`/register/`), this endpoint allows setting an arbitrary role."
        ),
        request=UserCreateSerializer,
        responses={
            201: OpenApiResponse(response=UserSerializer, description="User created."),
            400: OpenApiResponse(description="Validation error."),
            403: OpenApiResponse(description="Caller is not ADMIN."),
        },
    ),
)
class UserListCreateView(generics.ListCreateAPIView):
    """Liste et création des utilisateurs (ADMIN seulement)."""
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        queryset = User.objects.exclude(role=User.Role.ADMIN)
        role = self.request.query_params.get('role')
        is_active = self.request.query_params.get('is_active')
        search = self.request.query_params.get('search')

        if role:
            queryset = queryset.filter(role=role)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if search:
            queryset = queryset.filter(
                models.Q(nom__icontains=search) | 
                models.Q(prenom__icontains=search) | 
                models.Q(email__icontains=search)
            )
        return queryset.order_by('-date_creation')

    def perform_create(self, serializer):
        user = serializer.save()
        log_action(
            self.request.user,
            AuditLog.Action.CREATE,
            user.email,
            get_client_ip(self.request),
            {'role': user.role, 'nom': user.nom, 'prenom': user.prenom}
        )


@extend_schema_view(
    retrieve=extend_schema(
        tags=["Admin Users"],
        summary="Get user detail",
        description="Retrieves full details for a specific user by UUID. **ADMIN role required.**",
        responses={
            200: UserSerializer,
            403: OpenApiResponse(description="Caller is not ADMIN."),
            404: OpenApiResponse(description="User not found."),
        },
    ),
    update=extend_schema(
        tags=["Admin Users"],
        summary="Update user (full replace)",
        description="Full update of a user record. **ADMIN role required.**",
        request=UserUpdateSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description="Validation error."),
            403: OpenApiResponse(description="Caller is not ADMIN."),
            404: OpenApiResponse(description="User not found."),
        },
    ),
    partial_update=extend_schema(
        tags=["Admin Users"],
        summary="Partially update user",
        description=(
            "Partial update of a user record (PATCH). **ADMIN role required.**\n\n"
            "Editable fields: `nom`, `prenom`, `email`, `role`, `is_active`, `fonction`."
        ),
        request=UserUpdateSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description="Validation error."),
            403: OpenApiResponse(description="Caller is not ADMIN."),
            404: OpenApiResponse(description="User not found."),
        },
    ),
    destroy=extend_schema(
        tags=["Admin Users"],
        summary="Delete user",
        description=(
            "Permanently deletes a user by UUID. **ADMIN role required.**\n\n"
            "**Cannot delete ADMIN accounts** — returns `403` if the target user has role `ADMIN`."
        ),
        responses={
            200: OpenApiResponse(
                description="User deleted.",
                examples=[OpenApiExample("Deleted", value={"message": "Utilisateur supprimé."}, response_only=True)]
            ),
            403: OpenApiResponse(description="Caller is not ADMIN, or target is an ADMIN account."),
            404: OpenApiResponse(description="User not found."),
        },
    ),
)
class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Détail, modification et suppression d'un utilisateur (ADMIN seulement)."""
    permission_classes = [IsAdmin]
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer

    def perform_update(self, serializer):
        old_data = {
            'nom': serializer.instance.nom,
            'prenom': serializer.instance.prenom,
            'role': serializer.instance.role,
            'is_active': serializer.instance.is_active,
        }
        user = serializer.save()
        log_action(
            self.request.user,
            AuditLog.Action.UPDATE,
            user.email,
            get_client_ip(self.request),
            {'avant': old_data, 'apres': {
                'nom': user.nom,
                'prenom': user.prenom,
                'role': user.role,
                'is_active': user.is_active,
            }}
        )

    def perform_destroy(self, instance):
        email = instance.email
        log_action(
            self.request.user,
            AuditLog.Action.DELETE,
            email,
            get_client_ip(self.request),
            {'nom': instance.nom, 'prenom': instance.prenom, 'role': instance.role}
        )
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.role == User.Role.ADMIN:
            return Response(
                {'error': 'Impossible de supprimer un administrateur.'},
                status=status.HTTP_403_FORBIDDEN
            )
        self.perform_destroy(instance)
        return Response({'message': 'Utilisateur supprimé.'}, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Admin Users"],
    summary="Toggle user active status",
    description=(
        "Toggles the `is_active` field of a user (enable ↔ disable). **ADMIN role required.**\n\n"
        "**Cannot deactivate ADMIN accounts** — returns `403` if the target user has role `ADMIN`.\n\n"
        "Deactivating an account blocks future logins (`authenticate()` returns `None` for inactive users). "
        "Existing JWT sessions will still work until the access token expires (10 min), "
        "after which refresh will fail silently and the user will be logged out."
    ),
    request=None,
    responses={
        200: OpenApiResponse(
            description="Status toggled successfully.",
            examples=[
                OpenApiExample(
                    "Activated",
                    value={"message": "Utilisateur activé.", "is_active": True},
                    response_only=True,
                ),
                OpenApiExample(
                    "Deactivated",
                    value={"message": "Utilisateur désactivé.", "is_active": False},
                    response_only=True,
                ),
            ]
        ),
        403: OpenApiResponse(description="Caller is not ADMIN, or target is an ADMIN account."),
        404: OpenApiResponse(description="User not found."),
    },
)
class ToggleUserActiveView(generics.UpdateAPIView):
    """Activer/désactiver un utilisateur."""
    permission_classes = [IsAdmin]
    queryset = User.objects.all()

    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        if user.role == User.Role.ADMIN:
            return Response({'error': 'Action non autorisée sur un admin.'}, status=403)

        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])

        action = 'activated' if user.is_active else 'deactivated'
        log_action(
            request.user,
            AuditLog.Action.UPDATE,
            user.email,
            get_client_ip(request),
            {'action': action}
        )

        return Response({
            'message': f'Utilisateur {"activé" if user.is_active else "désactivé"}.',
            'is_active': user.is_active
        })


# ── Password Reset Views ──────────────────────────────────────────────────

@extend_schema(
    tags=["Password Reset"],
    summary="Request password reset email",
    description=(
        "Sends a password reset link to the provided email address.\n\n"
        "**Security:** Always returns the same success response regardless of whether "
        "the email exists in the database — this prevents user enumeration attacks.\n\n"
        "The reset link contains a UUID token valid for **24 hours**:\n"
        "`<FRONTEND_URL>/reset-password?token=<uuid>`\n\n"
        "**Development note:** If email sending fails and `DEBUG=True`, the response "
        "includes `token_debug` with the raw UUID for testing purposes. "
        "This field is `null` in production."
    ),
    request=PasswordResetRequestSerializer,
    auth=[],  # Public endpoint
    responses={
        200: OpenApiResponse(
            description="Request processed (same response whether email exists or not).",
            examples=[
                OpenApiExample(
                    "Success (email sent or not — same response)",
                    value={"status": "success", "message": "Si l'email existe, un lien de réinitialisation a été envoyé."},
                    response_only=True,
                )
            ]
        ),
        400: OpenApiResponse(description="Invalid email format."),
    },
)
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
            # Create token
            token = PasswordResetToken.objects.create(
                user=user,
                expire_le=timezone.now() + timedelta(hours=24)
            )
            
            # Envoi de l'email réel
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token.token}"
            subject = "Réinitialisation de votre mot de passe - crmPfe"
            message = f"Bonjour {user.prenom},\n\nPour réinitialiser votre mot de passe, cliquez sur le lien suivant :\n{reset_url}\n\nCe lien expirera dans 24 heures.\n\nSi vous n'avez pas demandé cette modification, vous pouvez ignorer cet e-mail."
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                logger.info(f"Email de réinitialisation envoyé à {email}")
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de l'email à {email}: {str(e)}")
                # En développement, on peut vouloir voir le token si le mail échoue
                return Response({
                    "status": "warning",
                    "message": "Erreur lors de l'envoi de l'email, mais le token a été généré.",
                    "token_debug": str(token.token) if settings.DEBUG else None
                })
            
            return Response({
                "status": "success", 
                "message": "Si l'email existe, un lien de réinitialisation a été envoyé."
            })
        except User.DoesNotExist:
            # Sécurité: ne pas révéler si l'email existe
            return Response({
                "status": "success", 
                "message": "Si l'email existe, un lien de réinitialisation a été envoyé."
            })


@extend_schema(
    tags=["Password Reset"],
    summary="Confirm password reset with token",
    description=(
        "Sets a new password using the UUID token received in the password reset email.\n\n"
        "**Token validation:**\n"
        "- Must match a valid `PasswordResetToken` record\n"
        "- Must not be expired (24-hour window)\n"
        "- Must not have been used already (`est_utilise = False`)\n\n"
        "After use, the token is marked as consumed and cannot be reused."
    ),
    request=PasswordResetConfirmSerializer,
    auth=[],  # Public endpoint — token in body is the credential
    responses={
        200: OpenApiResponse(
            description="Password reset successfully.",
            examples=[
                OpenApiExample(
                    "Success",
                    value={"status": "success", "message": "Mot de passe réinitialisé avec succès."},
                    response_only=True,
                )
            ]
        ),
        400: OpenApiResponse(
            description="Token expired, already used, passwords don't match, or weak password.",
            examples=[
                OpenApiExample(
                    "Expired token",
                    value={"error": "Le jeton a expiré."},
                    response_only=True,
                ),
                OpenApiExample(
                    "Invalid or used token",
                    value={"error": "Jeton invalide ou déjà utilisé."},
                    response_only=True,
                ),
            ]
        ),
    },
)
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token_uuid = serializer.validated_data['token']
        password = serializer.validated_data['password']

        try:
            token_obj = PasswordResetToken.objects.get(token=token_uuid, est_utilise=False)
            if not token_obj.is_valid:
                return Response({"error": "Le jeton a expiré."}, status=status.HTTP_400_BAD_REQUEST)
            
            user = token_obj.user
            user.set_password(password)
            user.save()
            
            token_obj.est_utilise = True
            token_obj.save()
            
            log_action(user, AuditLog.Action.UPDATE, user.email, get_client_ip(request), {"action": "password_reset"})
            
            return Response({"status": "success", "message": "Mot de passe réinitialisé avec succès."})
        except PasswordResetToken.DoesNotExist:
            return Response({"error": "Jeton invalide ou déjà utilisé."}, status=status.HTTP_400_BAD_REQUEST)
