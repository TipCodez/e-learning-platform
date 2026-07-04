from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.core.mail import send_mail
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.urls import reverse

from accounts.models import CustomUser

EMAIL_VERIFICATION_MAX_AGE = 60 * 60 * 24


def make_email_verification_token(user):
    signer = TimestampSigner()
    return signer.sign(str(user.pk))


def verify_email_token(token):
    signer = TimestampSigner()
    user_id = signer.unsign(token, max_age=EMAIL_VERIFICATION_MAX_AGE)
    return CustomUser.objects.get(pk=user_id)


def send_verification_email(request, user):
    token = make_email_verification_token(user)
    path = reverse("accounts:verify_email", kwargs={"token": token})
    verify_url = request.build_absolute_uri(path)
    subject = "Verify your Acadeval email"
    message = (
        f"Hi {user.get_full_name() or user.username},\n\n"
        f"Verify your Acadeval account using this link:\n{verify_url}\n\n"
        "This link expires in 24 hours."
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)


def token_error_message(exc):
    if isinstance(exc, SignatureExpired):
        return "That verification link has expired. Please request a new one."
    if isinstance(exc, BadSignature):
        return "That verification link is invalid."
    return "We could not verify that email address."


def send_password_setup_email(request, user, organization=None):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    path = reverse("accounts:password_reset_confirm", kwargs={"uidb64": uid, "token": token})
    setup_url = request.build_absolute_uri(path)
    org_name = organization.get_full_name() or organization.email if organization else "your organization"
    subject = "Set up your Acadeval learner account"
    message = (
        f"Hi {user.get_full_name() or user.email},\n\n"
        f"{org_name} added you to Acadeval as a learner.\n\n"
        f"Set your password using this secure link:\n{setup_url}\n\n"
        "After setting your password, sign in with your email address. "
        "If you were not expecting this invitation, you can ignore this email."
    )
    return send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
