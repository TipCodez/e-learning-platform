from django.conf import settings
from django.db import models


class OrganizationLearner(models.Model):
    organization = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="organization_learners")
    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="organization_memberships")
    department = models.CharField(max_length=120, blank=True)
    active = models.BooleanField(default=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("organization", "learner")


class OrganizationEnrollment(models.Model):
    organization = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="organization_course_enrollments")
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="organization_enrollments")
    learners = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="bulk_course_enrollments", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.organization} - {self.course}"


class OrganizationReport(models.Model):
    organization = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="organization_reports")
    title = models.CharField(max_length=180)
    summary = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
