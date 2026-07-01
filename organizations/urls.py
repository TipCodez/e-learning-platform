from django.urls import path

from organizations import views

app_name = "organizations"

urlpatterns = [
    path("learners/", views.learners, name="learners"),
]
