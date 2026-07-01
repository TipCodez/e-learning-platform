from django.contrib.auth.backends import ModelBackend

from accounts.models import CustomUser


class EmailAuthenticationBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = kwargs.get("email") or username
        if not email or not password:
            return None

        try:
            user = CustomUser.objects.get(email__iexact=email.strip())
        except CustomUser.DoesNotExist:
            CustomUser().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
