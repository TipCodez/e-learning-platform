from django.contrib import admin

from learning_paths.models import LearningPath, LearningPathCourse


class LearningPathCourseInline(admin.TabularInline):
    model = LearningPathCourse
    extra = 0


@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    list_display = ("title", "career_outcome", "estimated_duration", "is_featured")
    inlines = [LearningPathCourseInline]
