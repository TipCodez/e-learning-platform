from django.conf import settings
from django.core.mail import send_mail

from notifications.models import Notification


def notify_user(user, *, title, message, notification_type=Notification.Type.SYSTEM, link="", send_email=True):
    notification, created = Notification.objects.get_or_create(
        user=user,
        title=title,
        notification_type=notification_type,
        link=link,
        defaults={"message": message},
    )
    if not created and notification.message != message:
        notification.message = message
        notification.save(update_fields=["message"])

    email_enabled = getattr(settings, "EMAIL_NOTIFICATIONS_ENABLED", True)
    if send_email and email_enabled and user.email and not notification.email_sent:
        sent = send_mail(
            subject=title,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
        if sent:
            notification.email_sent = True
            notification.save(update_fields=["email_sent"])
    return notification
