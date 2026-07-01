from django.urls import path

from courses import views

app_name = "courses"

urlpatterns = [
    path("", views.course_list, name="list"),
    path("categories/", views.categories, name="categories"),
    path("create/", views.create_course, name="create"),
    path("<slug:slug>/", views.course_detail, name="detail"),
    path("<slug:slug>/edit/", views.edit_course, name="edit"),
    path("<slug:slug>/modules/", views.manage_modules, name="manage_modules"),
    path("<slug:slug>/lessons/", views.manage_lessons, name="manage_lessons"),
    path("<slug:slug>/reviews/", views.submit_review, name="review"),
    path("<slug:slug>/lessons/<int:lesson_id>/", views.lesson_detail, name="lesson"),
    path("<slug:slug>/lessons/<int:lesson_id>/complete/", views.mark_lesson_complete, name="complete_lesson"),
]
