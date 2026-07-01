from django.contrib import admin

from notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "notification_type", "read", "email_sent", "created_at")
    list_filter = ("notification_type", "read", "email_sent")
    search_fields = ("title", "message", "user__username")
