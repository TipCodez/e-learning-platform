from django.core.cache import cache
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


class AuthThrottleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = CustomUser.objects.create_user(
            email="throttle@example.com",
            password="StrongPass12345",
            role=CustomUser.Role.STUDENT,
        )

    def tearDown(self):
        cache.clear()

    def test_failed_login_attempts_are_throttled(self):
        login_url = reverse("accounts:login")
        for _ in range(10):
            response = self.client.post(login_url, {"username": self.user.email, "password": "wrong-password"})
            self.assertEqual(response.status_code, 200)

        response = self.client.post(login_url, {"username": self.user.email, "password": "wrong-password"})
        self.assertEqual(response.status_code, 429)

    def test_successful_login_clears_failed_attempt_counter(self):
        login_url = reverse("accounts:login")
        for _ in range(9):
            self.client.post(login_url, {"username": self.user.email, "password": "wrong-password"})

        response = self.client.post(login_url, {"username": self.user.email, "password": "StrongPass12345"})
        self.assertRedirects(response, reverse("dashboards:home"), fetch_redirect_response=False)
        self.client.logout()

        response = self.client.post(login_url, {"username": self.user.email, "password": "wrong-password"})
        self.assertEqual(response.status_code, 200)

    def test_registration_posts_are_throttled(self):
        register_url = reverse("accounts:register")
        payload = {
            "first_name": "Too",
            "last_name": "Many",
            "email": "too-many@example.com",
            "role": CustomUser.Role.STUDENT,
            "terms_accepted": "on",
            "password1": "short",
            "password2": "short",
        }
        for _ in range(5):
            response = self.client.post(register_url, payload)
            self.assertEqual(response.status_code, 200)

        response = self.client.post(register_url, payload)
        self.assertEqual(response.status_code, 429)

