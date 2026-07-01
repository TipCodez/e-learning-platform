from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render

from gamification.models import Badge, Leaderboard, LearningStreak, PointsTransaction


@login_required
def achievements(request):
    streak, _ = LearningStreak.objects.get_or_create(user=request.user)
    total_points = PointsTransaction.objects.filter(user=request.user).aggregate(total=Sum("points"))["total"] or 0
    return render(
        request,
        "gamification/achievements.html",
        {
            "badges": request.user.badges.select_related("badge"),
            "transactions": PointsTransaction.objects.filter(user=request.user)[:20],
            "available_badges": Badge.objects.filter(is_active=True),
            "streak": streak,
            "total_points": total_points,
        },
    )


def leaderboard(request):
    entries = Leaderboard.objects.select_related("user").order_by("rank", "-points")[:50]
    return render(request, "gamification/leaderboard.html", {"entries": entries})
