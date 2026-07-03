from django.urls import path

from notifications import views

app_name = "notifications"

urlpatterns = [
    path("", views.notification_list, name="list"),
    path("read-all/", views.mark_all_read, name="read_all"),
    path("<int:notification_id>/read/", views.mark_read, name="mark_read"),
]
