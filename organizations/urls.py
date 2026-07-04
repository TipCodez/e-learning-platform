from django.urls import path

from organizations import views

app_name = "organizations"

urlpatterns = [
    path("learners/", views.learners, name="learners"),
    path("learners/bulk/", views.bulk_learners, name="bulk_learners"),
    path("learners/<int:learner_id>/performance/", views.learner_performance, name="learner_performance"),
    path("enroll/", views.bulk_enroll, name="bulk_enroll"),
    path("reports/", views.reports, name="reports"),
    path("reports/generate/", views.generate_report, name="generate_report"),
    path("reports/export/", views.export_report, name="export_report"),
]
