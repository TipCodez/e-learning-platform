from django.conf import settings
from django.db import models
from django.utils import timezone


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="enrollments")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    last_accessed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ("student", "course")
        ordering = ["-enrolled_at"]

    def __str__(self):
        return f"{self.student} in {self.course}"


class LessonProgress(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="lesson_progress")
    lesson = models.ForeignKey("courses.Lesson", on_delete=models.CASCADE, related_name="progress_records")
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)
    last_viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("enrollment", "lesson")

    def mark_complete(self):
        self.completed = True
        self.completed_at = timezone.now()
        self.save(update_fields=["completed", "completed_at", "last_viewed_at"])


class CourseProgress(models.Model):
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name="progress")
    percentage = models.PositiveSmallIntegerField(default=0)
    completed_lessons = models.PositiveIntegerField(default=0)
    total_lessons = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def recalculate(self):
        self.total_lessons = self.enrollment.course.modules.aggregate(total=models.Count("lessons"))["total"] or 0
        self.completed_lessons = self.enrollment.lesson_progress.filter(completed=True).count()
        self.percentage = int((self.completed_lessons / self.total_lessons) * 100) if self.total_lessons else 0
        self.save()
        if self.percentage >= 100 and self.enrollment.status != Enrollment.Status.COMPLETED:
            self.enrollment.status = Enrollment.Status.COMPLETED
            self.enrollment.completed_at = timezone.now()
            self.enrollment.save(update_fields=["status", "completed_at"])
