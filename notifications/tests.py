from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import CustomUser
from courses.models import Course
from enrollments.models import Enrollment
from notifications.models import Notification
from notifications.services import notify_user


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", EMAIL_NOTIFICATIONS_ENABLED=True)
class NotificationServiceTests(TestCase):
    def test_notify_user_creates_in_app_notification_and_sends_email(self):
        user = CustomUser.objects.create_user(email="notify@example.com", password="Password12345")
        notification = notify_user(
            user,
            title="Welcome",
            message="Your notification is ready.",
            notification_type=Notification.Type.SYSTEM,
            link="/dashboard/",
        )
        self.assertEqual(Notification.objects.count(), 1)
        self.assertTrue(notification.email_sent)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["notify@example.com"])

    @override_settings(EMAIL_NOTIFICATIONS_ENABLED=False)
    def test_notify_user_respects_email_toggle(self):
        user = CustomUser.objects.create_user(email="silent@example.com", password="Password12345")
        notification = notify_user(user, title="Silent", message="In app only.")
        self.assertFalse(notification.email_sent)
        self.assertEqual(len(mail.outbox), 0)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", EMAIL_NOTIFICATIONS_ENABLED=True)
class NotificationFlowTests(TestCase):
    def setUp(self):
        self.instructor = CustomUser.objects.create_user(
            email="teacher.notifications@example.com",
            password="Password12345",
            role=CustomUser.Role.INSTRUCTOR,
        )
        self.learner = CustomUser.objects.create_user(
            email="learner.notifications@example.com",
            password="Password12345",
            role=CustomUser.Role.STUDENT,
        )
        self.admin = CustomUser.objects.create_user(
            email="admin.notifications@example.com",
            password="Password12345",
            role=CustomUser.Role.ADMIN,
            is_staff=True,
        )
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="Notification Driven Django",
            description="A course for notification tests.",
            status=Course.Status.PUBLISHED,
        )

    def test_enrollment_notifies_learner_and_instructor(self):
        self.client.force_login(self.learner)
        response = self.client.get(reverse("enrollments:enroll", args=[self.course.slug]))
        self.assertRedirects(response, reverse("courses:detail", args=[self.course.slug]))
        self.assertTrue(Enrollment.objects.filter(student=self.learner, course=self.course).exists())
        self.assertEqual(Notification.objects.filter(notification_type=Notification.Type.ENROLLMENT).count(), 2)
        self.assertEqual(len(mail.outbox), 2)

    def test_course_approval_notifies_instructor(self):
        pending_course = Course.objects.create(
            instructor=self.instructor,
            title="Pending Notification Course",
            description="Waiting for approval.",
            status=Course.Status.PENDING,
        )
        self.client.force_login(self.admin)
        response = self.client.post(reverse("courses:approve", args=[pending_course.slug]))
        self.assertRedirects(response, reverse("courses:pending"))
        notification = Notification.objects.get(title="Course approved")
        self.assertEqual(notification.user, self.instructor)
        self.assertTrue(notification.email_sent)
        self.assertEqual(len(mail.outbox), 1)
