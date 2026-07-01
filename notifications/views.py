from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


@login_required
def notification_list(request):
    return render(request, "notifications/list.html", {"notifications": request.user.notifications.all()})


@login_required
def mark_all_read(request):
    request.user.notifications.update(read=True)
    return redirect("notifications:list")
