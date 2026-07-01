from django.urls import path

from discussions import views

app_name = "discussions"

urlpatterns = [
    path("", views.discussion_list, name="list"),
    path("new/", views.create_discussion, name="create"),
    path("courses/<slug:slug>/new/", views.create_discussion, name="create_for_course"),
    path("<int:discussion_id>/", views.discussion_detail, name="detail"),
    path("<int:discussion_id>/reply/", views.reply, name="reply"),
    path("<int:discussion_id>/vote/", views.vote, name="vote"),
    path("<int:discussion_id>/report/", views.report, name="report"),
]