from django.urls import path
from .views import (
    RegisterView, LoginView, LogoutView, RefreshView, MeView,
    UserListCreateView, UserDetailView, ToggleUserActiveView,
    PasswordResetRequestView, PasswordResetConfirmView, ChangePasswordView
)
app_name = 'users'
urlpatterns = [
    # Auth
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', RefreshView.as_view(), name='refresh'),
    path('me/', MeView.as_view(), name='me'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),

    # Admin User Management
    path('admin/users/', UserListCreateView.as_view(), name='user-list-create'),
    path('admin/users/<uuid:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('admin/users/<uuid:pk>/toggle-active/', ToggleUserActiveView.as_view(), name='user-toggle-active'),
]
