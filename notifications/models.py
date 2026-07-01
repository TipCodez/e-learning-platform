from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        ENROLLMENT = "enrollment", "Enrollment"
        ASSIGNMENT_FEEDBACK = "assignment_feedback", "Assignment Feedback"
        CERTIFICATE = "certificate", "Certificate"
        PAYMENT = "payment", "Payment"
        INSTRUCTOR_APPROVAL = "instructor_approval", "Instructor Approval"
        SYSTEM = "system", "System"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=160)
    message = models.TextField()
    notification_type = models.CharField(max_length=40, choices=Type.choices, default=Type.SYSTEM)
    link = models.CharField(max_length=255, blank=True)
    read = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
