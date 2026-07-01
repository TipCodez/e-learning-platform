import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse


class Certificate(models.Model):
    certificate_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="certificates")
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="certificates")
    instructor_name = models.CharField(max_length=180)
    issue_date = models.DateField(auto_now_add=True)
    pdf_file = models.FileField(upload_to="certificates/", blank=True, null=True)
    qr_code = models.ImageField(upload_to="certificate-qr/", blank=True, null=True)
    is_revoked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "course")
        ordering = ["-issue_date"]

    def __str__(self):
        return f"{self.student} - {self.course}"

    def verification_url(self):
        return reverse("certificates:verify", kwargs={"certificate_id": self.certificate_id})


class CertificateTemplate(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
