from django.test import TestCase
from django.urls import reverse

from accounts.forms import RegisterForm
from accounts.models import CustomUser


class RegistrationTests(TestCase):
    def test_register_form_does_not_expose_username(self):
        form = RegisterForm()
        self.assertNotIn("username", form.fields)

    def test_user_can_register_with_email_and_password(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "first_name": "Ada",
                "last_name": "Lovelace",
                "email": "ada@example.com",
                "role": CustomUser.Role.STUDENT,
                "phone_number": "",
                "country": "Ghana",
                "terms_accepted": "on",
                "password1": "StrongPass12345",
                "password2": "StrongPass12345",
            },
        )
        self.assertRedirects(response, reverse("accounts:profile_setup"))
        user = CustomUser.objects.get(email="ada@example.com")
        self.assertTrue(user.check_password("StrongPass12345"))
        self.assertTrue(user.username)

    def test_duplicate_email_is_rejected(self):
        CustomUser.objects.create_user(username="ada", email="ada@example.com", password="StrongPass12345")
        form = RegisterForm(
            data={
                "first_name": "Ada",
                "last_name": "Again",
                "email": "ADA@example.com",
                "role": CustomUser.Role.STUDENT,
                "terms_accepted": "on",
                "password1": "StrongPass12345",
                "password2": "StrongPass12345",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
