from django.urls import path

from dashboards import views

app_name = "dashboards"

urlpatterns = [
    path("", views.dashboard_home, name="home"),
    path("student/", views.student_dashboard, name="student"),
    path("instructor/", views.instructor_dashboard, name="instructor"),
    path("instructor/analytics/", views.instructor_analytics, name="instructor_analytics"),
    path("instructor/earnings/", views.instructor_earnings, name="instructor_earnings"),
    path("organization/", views.organization_dashboard, name="organization"),
    path("admin/", views.admin_dashboard, name="admin"),
]