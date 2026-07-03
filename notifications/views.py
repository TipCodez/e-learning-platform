from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST


@login_required
def notification_list(request):
    return render(request, "notifications/list.html", {"notifications": request.user.notifications.all()})


@login_required
@require_POST
def mark_all_read(request):
    request.user.notifications.update(read=True)
    return redirect("notifications:list")


@login_required
@require_POST
def mark_read(request, notification_id):
    notification = get_object_or_404(request.user.notifications, id=notification_id)
    notification.read = True
    notification.save(update_fields=["read"])
    return redirect(notification.link or "notifications:list")
