from django.urls import path

from discussions import views

app_name = "discussions"

urlpatterns = [
    path("", views.discussion_list, name="list"),
    path("new/", views.create_discussion, name="create"),
    path("<int:discussion_id>/", views.discussion_detail, name="detail"),
    path("<int:discussion_id>/reply/", views.reply, name="reply"),
]
