from django.db import models
from django.utils.text import slugify


class LearningPath(models.Model):
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=210, unique=True, blank=True)
    description = models.TextField()
    career_outcome = models.CharField(max_length=180, blank=True)
    estimated_duration = models.CharField(max_length=80, blank=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class LearningPathCourse(models.Model):
    learning_path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, related_name="path_courses")
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="learning_paths")
    order = models.PositiveIntegerField(default=1)
    is_required = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]
        unique_together = ("learning_path", "course")
