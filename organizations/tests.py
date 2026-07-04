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

from assessments.models import Assignment, AssignmentSubmission, Quiz, QuizAttempt
from courses.models import Course, Lesson, Module
from enrollments.models import CourseProgress, Enrollment, LessonProgress


class OrganizationPerformanceReportTests(TestCase):
    def setUp(self):
        self.organization = CustomUser.objects.create_user(
            email="reports.org@example.com",
            password="Password12345",
            role=CustomUser.Role.ORGANIZATION,
        )
        self.other_organization = CustomUser.objects.create_user(
            email="other.org@example.com",
            password="Password12345",
            role=CustomUser.Role.ORGANIZATION,
        )
        self.instructor = CustomUser.objects.create_user(
            email="reports.teacher@example.com",
            password="Password12345",
            role=CustomUser.Role.INSTRUCTOR,
        )
        self.learner = CustomUser.objects.create_user(email="reports.learner@example.com", password="Password12345")
        self.other_learner = CustomUser.objects.create_user(email="other.learner@example.com", password="Password12345")
        OrganizationLearner.objects.create(organization=self.organization, learner=self.learner, department="Security")
        OrganizationLearner.objects.create(organization=self.other_organization, learner=self.other_learner)
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="Canvas Style Reporting",
            description="Reporting course",
            status=Course.Status.PUBLISHED,
        )
        module = Module.objects.create(course=self.course, title="Module 1", order=1)
        lesson = Lesson.objects.create(module=module, title="Lesson 1", order=1)
        enrollment = Enrollment.objects.create(student=self.learner, course=self.course)
        CourseProgress.objects.create(enrollment=enrollment, percentage=50, completed_lessons=1, total_lessons=2)
        LessonProgress.objects.create(enrollment=enrollment, lesson=lesson, completed=True)
        quiz = Quiz.objects.create(course=self.course, title="Checkpoint")
        QuizAttempt.objects.create(quiz=quiz, student=self.learner, score=88, passed=True)
        assignment = Assignment.objects.create(course=self.course, title="Lab", instructions="Submit work")
        AssignmentSubmission.objects.create(assignment=assignment, student=self.learner, score=92, feedback="Good work")

    def test_reports_show_learner_progress_scores_and_lessons(self):
        self.client.force_login(self.organization)
        response = self.client.get(reverse("organizations:reports"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "reports.learner@example.com")
        self.assertContains(response, "50.0%")
        self.assertContains(response, "88.0%")
        self.assertContains(response, "92")
        self.assertContains(response, "1 completed")

    def test_learner_performance_detail_is_scoped_to_organization(self):
        self.client.force_login(self.organization)
        response = self.client.get(reverse("organizations:learner_performance", args=[self.learner.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Canvas Style Reporting")
        self.assertContains(response, "Checkpoint")
        self.assertContains(response, "Lab")

        blocked = self.client.get(reverse("organizations:learner_performance", args=[self.other_learner.id]))
        self.assertEqual(blocked.status_code, 404)

    def test_export_contains_performance_columns(self):
        self.client.force_login(self.organization)
        response = self.client.get(reverse("organizations:export_report"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("completed_lessons", content)
        self.assertIn("quiz_average", content)
        self.assertIn("assignment_average", content)
        self.assertIn("reports.learner@example.com", content)
