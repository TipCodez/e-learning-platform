from django.urls import path

from learning_paths import views

app_name = "learning_paths"

urlpatterns = [
    path("", views.path_list, name="list"),
    path("<slug:slug>/", views.path_detail, name="detail"),
]
