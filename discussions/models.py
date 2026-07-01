from django.conf import settings
from django.db import models


class Discussion(models.Model):
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="discussions")
    lesson = models.ForeignKey("courses.Lesson", on_delete=models.SET_NULL, blank=True, null=True, related_name="discussions")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="discussions")
    title = models.CharField(max_length=180)
    body = models.TextField()
    upvotes = models.PositiveIntegerField(default=0)
    is_reported = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class DiscussionReply(models.Model):
    discussion = models.ForeignKey(Discussion, on_delete=models.CASCADE, related_name="replies")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="discussion_replies")
    body = models.TextField()
    is_instructor_reply = models.BooleanField(default=False)
    is_reported = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class Announcement(models.Model):
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="announcements")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="announcements")
    title = models.CharField(max_length=180)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
