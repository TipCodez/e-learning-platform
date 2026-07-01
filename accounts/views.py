from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render

from accounts.forms import EmailAuthenticationForm, ProfileForm, RegisterForm
from accounts.tokens import send_verification_email, token_error_message, verify_email_token


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboards:home")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_verification_email(request, user)
            login(request, user, backend="accounts.backends.EmailAuthenticationBackend")
            messages.success(request, "Welcome to Acadeval. Your account is ready.")
            return redirect("accounts:profile_setup")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


class AcadevalLoginView(LoginView):
    authentication_form = EmailAuthenticationForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class AcadevalLogoutView(LogoutView):
    pass


@login_required
def profile_setup(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("dashboards:home")
    else:
        form = ProfileForm(instance=request.user)

    return render(request, "accounts/profile_setup.html", {"form": form})


@login_required
def profile(request):
    return render(request, "accounts/profile.html")


def verify_email(request, token):
    try:
        user = verify_email_token(token)
    except Exception as exc:
        messages.error(request, token_error_message(exc))
        return redirect("accounts:login")

    user.email_verified = True
    user.save(update_fields=["email_verified"])
    messages.success(request, "Your email address has been verified.")
    return redirect("dashboards:home" if request.user.is_authenticated else "accounts:login")
