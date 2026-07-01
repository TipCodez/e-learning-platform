from django.contrib.auth import views as auth_views
from django.urls import path
from django.urls import reverse_lazy

from accounts import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.AcadevalLoginView.as_view(), name="login"),
    path("logout/", views.AcadevalLogoutView.as_view(), name="logout"),
    path("verify-email/<path:token>/", views.verify_email, name="verify_email"),
    path("profile/setup/", views.profile_setup, name="profile_setup"),
    path("profile/", views.profile, name="profile"),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset.html",
            success_url=reverse_lazy("accounts:password_reset_done"),
            email_template_name="registration/password_reset_email.html",
            subject_template_name="registration/password_reset_subject.txt",
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url=reverse_lazy("accounts:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(template_name="accounts/password_reset_complete.html"),
        name="password_reset_complete",
    ),
]
