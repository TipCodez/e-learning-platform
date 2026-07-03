from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase, override_settings
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


class PublicMediaTests(TestCase):
    def test_public_media_serves_only_allowed_prefixes(self):
        with TemporaryDirectory() as temp_dir:
            media_root = Path(temp_dir)
            public_file = media_root / "blog-blocks" / "image.txt"
            private_file = media_root / "assignment-submissions" / "secret.txt"
            public_file.parent.mkdir(parents=True)
            private_file.parent.mkdir(parents=True)
            public_file.write_text("public", encoding="utf-8")
            private_file.write_text("private", encoding="utf-8")
            with override_settings(MEDIA_ROOT=media_root):
                public_response = self.client.get("/media/blog-blocks/image.txt")
                private_response = self.client.get("/media/assignment-submissions/secret.txt")
                public_response.close()
        self.assertEqual(public_response.status_code, 200)
        self.assertEqual(private_response.status_code, 404)
