from django.conf import settings
from django.db import models


class AIAssistantSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_assistant_sessions")
    course = models.ForeignKey("courses.Course", on_delete=models.SET_NULL, blank=True, null=True)
    prompt = models.TextField()
    response_placeholder = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
