from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from courses.models import Course, Lesson, Module
from enrollments.models import CourseProgress, Enrollment, LessonProgress


class PlatformSmokeFlowTests(TestCase):
    def setUp(self):
        self.instructor = CustomUser.objects.create_user(
            username="flow_teacher",
            email="flow.teacher@example.com",
            password="Password12345",
            role=CustomUser.Role.INSTRUCTOR,
        )
        self.learner = CustomUser.objects.create_user(
            username="flow_learner",
            email="flow.learner@example.com",
            password="Password12345",
            role=CustomUser.Role.STUDENT,
        )
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="Production Django Flow",
            description="A published course used by smoke tests.",
            status=Course.Status.PUBLISHED,
        )
        self.module = Module.objects.create(course=self.course, title="Start", order=1)
        self.lesson = Lesson.objects.create(
            module=self.module,
            title="First Lesson",
            content="Welcome to the course.",
            order=1,
            is_preview=False,
        )

    def test_health_endpoint_returns_json(self):
        response = self.client.get(reverse("health_check"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json()["status"], "ok")

    def test_registration_creates_account_and_auto_logs_in(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "first_name": "Grace",
                "last_name": "Hopper",
                "email": "grace@example.com",
                "role": CustomUser.Role.STUDENT,
                "phone_number": "",
                "country": "Ghana",
                "terms_accepted": "on",
                "password1": "StrongPass12345",
                "password2": "StrongPass12345",
            },
        )
        self.assertRedirects(response, reverse("accounts:profile_setup"))
        user = CustomUser.objects.get(email="grace@example.com")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.id)

    def test_email_and_password_login_reaches_dashboard(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": self.learner.email, "password": "Password12345"},
        )
        self.assertRedirects(response, reverse("dashboards:home"), fetch_redirect_response=False)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.learner.id)

    def test_protected_lesson_requires_enrollment(self):
        self.client.force_login(self.learner)
        response = self.client.get(reverse("courses:lesson", args=[self.course.slug, self.lesson.id]))
        self.assertRedirects(response, reverse("courses:detail", args=[self.course.slug]))
        self.assertFalse(LessonProgress.objects.exists())

    def test_enrolled_learner_can_complete_course_progress(self):
        enrollment = Enrollment.objects.create(student=self.learner, course=self.course)
        self.client.force_login(self.learner)
        response = self.client.post(reverse("courses:complete_lesson", args=[self.course.slug, self.lesson.id]))
        self.assertRedirects(response, reverse("courses:lesson", args=[self.course.slug, self.lesson.id]))
        progress = CourseProgress.objects.get(enrollment=enrollment)
        enrollment.refresh_from_db()
        self.assertEqual(progress.percentage, 100)
        self.assertEqual(progress.completed_lessons, 1)
        self.assertEqual(progress.total_lessons, 1)
        self.assertEqual(enrollment.status, Enrollment.Status.COMPLETED)




class DashboardRenderSmokeTests(TestCase):
    def test_role_dashboards_render(self):
        users_and_routes = [
            (
                CustomUser.objects.create_user(
                    email="dashboard.student@example.com",
                    password="Password12345",
                    role=CustomUser.Role.STUDENT,
                ),
                reverse("dashboards:student"),
            ),
            (
                CustomUser.objects.create_user(
                    email="dashboard.instructor@example.com",
                    password="Password12345",
                    role=CustomUser.Role.INSTRUCTOR,
                ),
                reverse("dashboards:instructor"),
            ),
            (
                CustomUser.objects.create_user(
                    email="dashboard.organization@example.com",
                    password="Password12345",
                    role=CustomUser.Role.ORGANIZATION,
                ),
                reverse("dashboards:organization"),
            ),
            (
                CustomUser.objects.create_user(
                    email="dashboard.admin@example.com",
                    password="Password12345",
                    role=CustomUser.Role.ADMIN,
                    is_staff=True,
                ),
                reverse("dashboards:admin"),
            ),
        ]
        for user, url in users_and_routes:
            with self.subTest(route=url):
                self.client.force_login(user)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.client.logout()
