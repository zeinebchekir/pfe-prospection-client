"""
User model definitions for the auth system.

The default Django User is replaced entirely:
  - Authentication uses email (not username).
  - Role is a plain CharField, not a Django group.
  - Tokens are not stored here; token state lives in the SimpleJWT
    blacklist table and browser HTTP-only cookies.

Models:
  User              — the main account entity
  UserSession       — records active refresh token sessions (informational)
  PasswordResetToken — one-time tokens for the /password-reset/ flow
"""
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom manager that uses email instead of username for auth."""

    def create_user(self, email, password=None, **extra_fields):
        """
        Create a regular user. Password is hashed via set_password (PBKDF2-SHA256).
        Always normalizes the email domain to lowercase.
        """
        if not email:
            raise ValueError('Email obligatoire')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # Hashes password — never stored in plaintext
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create a superuser with ADMIN role and Django staff/superuser flags."""
        extra_fields.setdefault('role', User.Role.ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model. Replaces Django's default User entirely.

    Authentication:
      - USERNAME_FIELD = 'email' (no username field exists)
      - Password is hashed by Django (PBKDF2-SHA256 by default)
      - Login is handled by Django's authenticate() in LoginView

    Authorization:
      - Role determines accessible routes and API endpoints
      - Role is set at creation; only ADMIN can change another user's role
      - is_active = False blocks login entirely (authenticate() returns None)
    """

    class Role(models.TextChoices):
        """Possible values for the role field. Used for both DB storage and permission checks."""
        ADMIN = 'ADMIN', 'Administrateur'
        CEO = 'CEO', 'CEO'
        COMMERCIAL = 'COMMERCIAL', 'Commercial'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.COMMERCIAL)
    fonction = models.CharField(max_length=100, blank=True)
    equipe_id = models.UUIDField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_creation = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom', 'prenom']

    class Meta:
        db_table = 'users'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.email})"

    @property
    def full_name(self):
        """Convenience property used by UserProfileSerializer."""
        return f"{self.prenom} {self.nom}"

    # Role helper methods — used in templates and permission checks
    def is_admin(self):
        return self.role == self.Role.ADMIN

    def is_ceo(self):
        return self.role == self.Role.CEO

    def is_commercial(self):
        return self.role == self.Role.COMMERCIAL


class UserSession(models.Model):
    """
    Records an active refresh token session per user.

    Note: This table is informational only. The actual token validity
    is enforced by the SimpleJWT blacklist (rest_framework_simplejwt.token_blacklist).
    Token rotation and blacklisting happen independently of this table.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    refresh_token = models.TextField(unique=True)
    adresse_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_expiration = models.DateTimeField()  # Set to REFRESH_TOKEN_LIFETIME from settings
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'user_sessions'
        verbose_name = 'Session utilisateur'

    def __str__(self):
        return f"Session de {self.user.email}"

    @property
    def is_expired(self):
        return timezone.now() > self.date_expiration


class PasswordResetToken(models.Model):
    """
    One-time UUID token for password reset.

    Flow:
      1. PasswordResetRequestView creates a token (24h expiry) and emails the link.
      2. PasswordResetConfirmView validates the token and sets the new password.
      3. est_utilise is set to True after use — tokens cannot be reused.

    The token UUID is sent in the password reset email URL:
      <FRONTEND_URL>/reset-password?token=<uuid>
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True)  # The value sent in the email link
    cree_le = models.DateTimeField(auto_now_add=True)
    expire_le = models.DateTimeField()  # Always set to now + 24h in PasswordResetRequestView
    est_utilise = models.BooleanField(default=False)  # Prevents token reuse

    class Meta:
        db_table = 'password_reset_tokens'
        verbose_name = 'Jeton de réinitialisation'

    def __str__(self):
        return f"Token reset pour {self.user.email}"

    @property
    def is_valid(self):
        return not self.est_utilise and timezone.now() < self.expire_le
