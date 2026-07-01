from django.contrib import admin

from gamification.models import Badge, Leaderboard, LearningStreak, PointsTransaction, UserBadge

admin.site.register(Badge)
admin.site.register(UserBadge)
admin.site.register(PointsTransaction)
admin.site.register(LearningStreak)
admin.site.register(Leaderboard)
