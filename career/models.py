from django.conf import settings
from django.db import models


class CareerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="career_profile")
    target_role = models.CharField(max_length=160, blank=True)
    skills = models.TextField(blank=True)
    experience_summary = models.TextField(blank=True)
    portfolio_url = models.URLField(blank=True)
    job_readiness_score = models.PositiveSmallIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Career profile: {self.user}"


class CVDocument(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cv_documents")
    title = models.CharField(max_length=160)
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class CoverLetter(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cover_letters")
    job_title = models.CharField(max_length=160)
    company = models.CharField(max_length=160, blank=True)
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SkillAssessment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="skill_assessments")
    skill = models.CharField(max_length=120)
    score = models.PositiveSmallIntegerField(default=0)
    recommendation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class InterviewPreparation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="interview_preparations")
    target_role = models.CharField(max_length=160)
    notes = models.TextField(blank=True)
    checklist_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
