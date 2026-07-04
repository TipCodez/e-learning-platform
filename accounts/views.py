from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render

from accounts.forms import EmailAuthenticationForm, ProfileForm, RegisterForm
from accounts.security import throttle_clear, throttle_hit, throttle_is_blocked
from accounts.tokens import send_verification_email, token_error_message, verify_email_token


LOGIN_THROTTLE_LIMIT = 10
LOGIN_THROTTLE_WINDOW = 10 * 60
REGISTER_THROTTLE_LIMIT = 5
REGISTER_THROTTLE_WINDOW = 60 * 60


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboards:home")

    if request.method == "POST":
        if throttle_hit("register", request, limit=REGISTER_THROTTLE_LIMIT, window=REGISTER_THROTTLE_WINDOW):
            messages.error(request, "Too many registration attempts. Please wait before trying again.")
            return render(request, "accounts/register.html", {"form": RegisterForm(request.POST)}, status=429)
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

    def _identifier(self):
        return self.request.POST.get("username", "").strip().lower()

    def dispatch(self, request, *args, **kwargs):
        if request.method == "POST" and throttle_is_blocked(
            "login",
            request,
            identifier=request.POST.get("username", "").strip().lower(),
            limit=LOGIN_THROTTLE_LIMIT,
        ):
            messages.error(request, "Too many failed login attempts. Please wait before trying again.")
            form = self.get_form()
            return self.render_to_response(self.get_context_data(form=form), status=429)
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        blocked = throttle_hit(
            "login",
            self.request,
            identifier=self._identifier(),
            limit=LOGIN_THROTTLE_LIMIT,
            window=LOGIN_THROTTLE_WINDOW,
        )
        response = super().form_invalid(form)
        if blocked:
            messages.error(self.request, "Too many failed login attempts. Please wait before trying again.")
            response.status_code = 429
        return response

    def form_valid(self, form):
        throttle_clear("login", self.request, identifier=self._identifier())
        return super().form_valid(form)


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

