from django.conf import settings
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
