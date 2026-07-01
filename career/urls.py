from django.urls import path

from career import views

app_name = "career"

urlpatterns = [
    path("", views.career_dashboard, name="dashboard"),
    path("profile/", views.profile, name="profile"),
    path("cv-builder/", views.cv_builder, name="cv_builder"),
    path("cover-letter/", views.cover_letter, name="cover_letter"),
    path("skill-assessment/", views.skill_assessment, name="skill_assessment"),
    path("interview-prep/", views.interview_prep, name="interview_prep"),
]
