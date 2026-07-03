from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from courses.models import Course
from payments.models import InstructorPayout, Payment


class InstructorPayoutTests(TestCase):
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
            title="Paid Django",
            description="Paid course",
            status=Course.Status.PUBLISHED,
            is_free=False,
            price=100,
        )

    def test_student_cannot_request_payout(self):
        self.client.force_login(self.learner)
        response = self.client.post(reverse("payments:request_payout"), {"payout_method": "Bank", "payout_account": "123"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(InstructorPayout.objects.exists())

    def test_instructor_can_request_available_payout(self):
        Payment.objects.create(
            user=self.learner,
            course=self.course,
            amount=100,
            gateway=Payment.Gateway.CARD,
            status=Payment.Status.SUCCESS,
            reference="PAY-TEST-1",
        )
        self.client.force_login(self.instructor)
        response = self.client.post(reverse("payments:request_payout"), {"payout_method": "Bank", "payout_account": "123"})
        self.assertEqual(response.status_code, 302)
        payout = InstructorPayout.objects.get()
        self.assertEqual(payout.status, InstructorPayout.Status.REQUESTED)
        self.assertEqual(payout.net_amount, 80)
