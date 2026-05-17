"""
Request/response serializers for the auth system.

Serializer hierarchy for user data:
  LoginSerializer            — validates login credentials (not a ModelSerializer)
  RegisterSerializer         — self-registration; forces role=COMMERCIAL on create
  UserProfileSerializer      — read-only profile returned on login/register/me
  ProfileUpdateSerializer    — allows user to edit own name/fonction (no role/email change)
  UserSerializer             — admin read view of user records
  UserCreateSerializer       — admin-only creation; allows any role
  UserUpdateSerializer       — admin-only edit; includes role and is_active
  ChangePasswordSerializer   — validates old+new+confirm password change
  PasswordResetRequest/ConfirmSerializer — password reset token flow

All password fields use Django's validate_password to enforce strength rules.
Password fields are always write_only=True and never appear in responses.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer pour la lecture des utilisateurs."""
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'nom', 'prenom', 'role',
            'is_active', 'date_creation', 'full_name'
        ]
        read_only_fields = ['id', 'date_creation', 'full_name']


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création d'un utilisateur par un admin.
    Unlike RegisterSerializer, the caller can assign any role.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        help_text="Password for the new account. Must pass Django's password validators (min length, common password check, etc.).",
    )
    email = serializers.EmailField(help_text="Unique email address. Used as the login username.")
    role = serializers.ChoiceField(
        choices=User.Role.choices,
        help_text="User role: ADMIN, CEO, or COMMERCIAL. COMMERCIAL is the default for self-registration.",
    )
    is_active = serializers.BooleanField(
        default=True,
        help_text="Whether the account is active. Inactive accounts cannot log in.",
    )

    class Meta:
        model = User
        fields = ['email', 'nom', 'prenom', 'role', 'password', 'is_active']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la modification d'un utilisateur par un admin."""
    role = serializers.ChoiceField(
        choices=User.Role.choices,
        help_text="New role to assign. Changing a user's role takes effect on next login.",
    )
    is_active = serializers.BooleanField(
        help_text="Set to false to block this user from logging in immediately.",
    )

    class Meta:
        model = User
        fields = ['nom', 'prenom', 'email', 'role', 'is_active', 'fonction']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer pour le profil de l'utilisateur connecté."""
    class Meta:
        model = User
        fields = ['id', 'email', 'nom', 'prenom', 'role', 'full_name', 'fonction']
        read_only_fields = ['id', 'email', 'role', 'full_name']


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la modification du profil par l'utilisateur lui-même.
    Only nom, prenom, and fonction are editable — role and email are immutable here.
    """
    nom = serializers.CharField(help_text="Last name of the user.")
    prenom = serializers.CharField(help_text="First name of the user.")
    fonction = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Job title or function (e.g. 'Account Manager'). Optional.",
    )

    class Meta:
        model = User
        fields = ['nom', 'prenom', 'fonction']


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer pour le changement de mot de passe."""
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        help_text="The user's current password for verification before accepting the new one.",
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        help_text="New password. Must pass Django's strength validators.",
    )
    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        help_text="Must exactly match new_password.",
    )

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Les mots de passe ne correspondent pas."})
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'auto-inscription (si autorisée).
    Role is always forced to COMMERCIAL — it cannot be set by the caller.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        help_text="Password for the new account. Must pass Django's validators.",
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        help_text="Password confirmation — must match password exactly.",
    )
    email = serializers.EmailField(help_text="Unique email address used as login.")
    nom = serializers.CharField(help_text="Last name.")
    prenom = serializers.CharField(help_text="First name.")

    class Meta:
        model = User
        fields = ['email', 'nom', 'prenom', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            nom=validated_data['nom'],
            prenom=validated_data['prenom'],
            role=User.Role.COMMERCIAL  # Par défaut lors de l'inscription
        )
        return user


class LoginSerializer(serializers.Serializer):
    """
    Validates the login request payload. This is not a ModelSerializer—
    it only checks that both fields are present. Credential verification
    (password hash check) is done by Django's authenticate() in LoginView.
    """
    email = serializers.EmailField(
        required=True,
        help_text="Registered email address.",
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        help_text="Account password.",
    )


class PasswordResetRequestSerializer(serializers.Serializer):
    """Validates the email field for a password reset request."""
    email = serializers.EmailField(
        required=True,
        help_text="Email address to send the reset link to.",
    )


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Validates the password reset confirmation payload.
    The token comes from the URL query parameter in the reset email link.
    """
    token = serializers.UUIDField(
        required=True,
        help_text="UUID token from the password reset email link (?token=<uuid>). Valid for 24 hours, single-use.",
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        help_text="New password. Must pass Django's strength validators.",
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        help_text="New password confirmation — must match password.",
    )

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs
