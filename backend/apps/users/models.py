import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email obligatoire')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', User.Role.ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
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
        return f"{self.prenom} {self.nom}"

    def is_admin(self):
        return self.role == self.Role.ADMIN

    def is_ceo(self):
        return self.role == self.Role.CEO

    def is_commercial(self):
        return self.role == self.Role.COMMERCIAL


class UserSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    refresh_token = models.TextField(unique=True)
    adresse_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_expiration = models.DateTimeField()
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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    cree_le = models.DateTimeField(auto_now_add=True)
    expire_le = models.DateTimeField()
    est_utilise = models.BooleanField(default=False)

    class Meta:
        db_table = 'password_reset_tokens'
        verbose_name = 'Jeton de réinitialisation'

    def __str__(self):
        return f"Token reset pour {self.user.email}"

    @property
    def is_valid(self):
        return not self.est_utilise and timezone.now() < self.expire_le
