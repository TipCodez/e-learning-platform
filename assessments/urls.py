from django.urls import path

from assessments import views

app_name = "assessments"

urlpatterns = [
    path("quizzes/<int:quiz_id>/", views.quiz_detail, name="quiz"),
    path("quiz-results/<int:attempt_id>/", views.quiz_result, name="quiz_result"),
    path("assignments/<int:assignment_id>/", views.assignment_detail, name="assignment"),
    path("submissions/", views.submission_queue, name="submissions"),
    path("submissions/<int:submission_id>/grade/", views.grade_submission, name="grade_submission"),
]