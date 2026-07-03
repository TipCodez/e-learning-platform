from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from core.models import BlogPost, FAQ
from courses.models import Course


class SearchTests(TestCase):
    def test_search_returns_public_content(self):
        instructor = CustomUser.objects.create_user(
            username="teacher",
            email="teacher@example.com",
            password="Password12345",
            role=CustomUser.Role.INSTRUCTOR,
        )
        Course.objects.create(instructor=instructor, title="Python Basics", description="Learn Python", status=Course.Status.PUBLISHED)
        BlogPost.objects.create(title="Python study guide", slug="python-study-guide", content="Practice daily", is_published=True)
        FAQ.objects.create(question="How do I learn Python?", answer="Start with basics.", is_active=True)
        response = self.client.get(reverse("core:search"), {"q": "Python"})
        self.assertContains(response, "Python Basics")
        self.assertContains(response, "Python study guide")
        self.assertContains(response, "How do I learn Python?")
