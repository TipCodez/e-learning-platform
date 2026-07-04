import re

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import CustomUser
from organizations.models import OrganizationLearner


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class BulkLearnerPasswordSetupTests(TestCase):
    def setUp(self):
        self.organization = CustomUser.objects.create_user(
            email="org@example.com",
            password="Password12345",
            role=CustomUser.Role.ORGANIZATION,
        )

    def test_bulk_created_learner_gets_password_setup_email(self):
        self.client.force_login(self.organization)
        response = self.client.post(
            reverse("organizations:bulk_learners"),
            {"emails": "new.learner@example.com", "department": "Engineering", "active": "on"},
        )
        self.assertEqual(response.status_code, 200)
        learner = CustomUser.objects.get(email="new.learner@example.com")
        self.assertFalse(learner.has_usable_password())
        self.assertTrue(OrganizationLearner.objects.filter(organization=self.organization, learner=learner).exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Set up your Acadeval learner account", mail.outbox[0].subject)
        self.assertIn("/accounts/reset/", mail.outbox[0].body)

    def test_bulk_password_setup_link_allows_learner_to_set_password(self):
        self.client.force_login(self.organization)
        self.client.post(reverse("organizations:bulk_learners"), {"emails": "setup.learner@example.com", "active": "on"})
        learner = CustomUser.objects.get(email="setup.learner@example.com")
        setup_url = re.search(r"http://testserver(?P<path>/accounts/reset/[^\s]+)", mail.outbox[0].body).group("path")

        self.client.logout()
        get_response = self.client.get(setup_url, follow=True)
        self.assertEqual(get_response.status_code, 200)
        post_url = get_response.redirect_chain[-1][0] if get_response.redirect_chain else setup_url
        response = self.client.post(
            post_url,
            {"new_password1": "LearnerStrongPass123", "new_password2": "LearnerStrongPass123"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        learner.refresh_from_db()
        self.assertTrue(learner.has_usable_password())
        self.assertTrue(self.client.login(username="setup.learner@example.com", password="LearnerStrongPass123"))

    def test_existing_bulk_learner_is_attached_without_password_email(self):
        learner = CustomUser.objects.create_user(email="existing.learner@example.com", password="Password12345")
        self.client.force_login(self.organization)
        response = self.client.post(reverse("organizations:bulk_learners"), {"emails": learner.email, "active": "on"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
        self.assertTrue(OrganizationLearner.objects.filter(organization=self.organization, learner=learner).exists())
