from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from courses.models import Course, Review
from enrollments.models import Enrollment


class CourseReviewSecurityTests(TestCase):
    def setUp(self):
        self.instructor = CustomUser.objects.create_user(
            username="teacher",
            email="teacher@example.com",
            password="Password12345",
            role=CustomUser.Role.INSTRUCTOR,
        )
        self.learner = CustomUser.objects.create_user(
            username="learner",
            email="learner@example.com",
            password="Password12345",
            role=CustomUser.Role.STUDENT,
        )
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="Secure Django",
            description="Security-first Django course",
            status=Course.Status.PUBLISHED,
        )

    def test_enrollment_required_to_review(self):
        self.client.force_login(self.learner)
        response = self.client.post(reverse("courses:review", args=[self.course.slug]), {"rating": 5, "comment": "Useful course."})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Review.objects.exists())

    def test_enrolled_learner_can_review_once(self):
        Enrollment.objects.create(student=self.learner, course=self.course)
        self.client.force_login(self.learner)
        self.client.post(reverse("courses:review", args=[self.course.slug]), {"rating": 5, "comment": "Useful course."})
        self.client.post(reverse("courses:review", args=[self.course.slug]), {"rating": 4, "comment": "Still useful."})
        self.assertEqual(Review.objects.count(), 1)
        self.assertEqual(Review.objects.get().rating, 4)

    def test_instructor_cannot_review_own_course(self):
        self.client.force_login(self.instructor)
        response = self.client.post(reverse("courses:review", args=[self.course.slug]), {"rating": 5, "comment": "Mine."})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Review.objects.exists())
