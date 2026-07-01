from django.urls import path

from gamification import views

app_name = "gamification"

urlpatterns = [
    path("", views.achievements, name="achievements"),
    path("leaderboard/", views.leaderboard, name="leaderboard"),
]
