from django.urls import path

from enrollments import views

app_name = "enrollments"

urlpatterns = [
    path("my-courses/", views.my_courses, name="my_courses"),
    path("continue/", views.continue_learning, name="continue_learning"),
    path("enroll/<slug:slug>/", views.enroll, name="enroll"),
]
