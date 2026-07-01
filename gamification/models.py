from django.conf import settings
from django.db import models
from django.utils import timezone


class Badge(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=80, blank=True)
    points_required = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="badges")
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name="users")
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "badge")


class PointsTransaction(models.Model):
    class Reason(models.TextChoices):
        LESSON_COMPLETED = "lesson_completed", "Lesson Completed"
        QUIZ_PASSED = "quiz_passed", "Quiz Passed"
        COURSE_COMPLETED = "course_completed", "Course Completed"
        CERTIFICATE_EARNED = "certificate_earned", "Certificate Earned"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="points_transactions")
    points = models.IntegerField()
    reason = models.CharField(max_length=40, choices=Reason.choices)
    description = models.CharField(max_length=180, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class LearningStreak(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="learning_streak")
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(blank=True, null=True)

    def record_activity(self):
        today = timezone.localdate()
        if self.last_activity_date == today:
            return
        if self.last_activity_date and (today - self.last_activity_date).days == 1:
            self.current_streak += 1
        else:
            self.current_streak = 1
        self.longest_streak = max(self.longest_streak, self.current_streak)
        self.last_activity_date = today
        self.save()


class Leaderboard(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="leaderboard_entry")
    points = models.PositiveIntegerField(default=0)
    rank = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
