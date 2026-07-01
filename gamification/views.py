from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from gamification.models import Badge, Leaderboard, PointsTransaction


@login_required
def achievements(request):
    return render(
        request,
        "gamification/achievements.html",
        {
            "badges": request.user.badges.select_related("badge"),
            "transactions": PointsTransaction.objects.filter(user=request.user)[:20],
            "available_badges": Badge.objects.filter(is_active=True),
        },
    )


def leaderboard(request):
    entries = Leaderboard.objects.select_related("user").order_by("rank", "-points")[:50]
    return render(request, "gamification/leaderboard.html", {"entries": entries})
