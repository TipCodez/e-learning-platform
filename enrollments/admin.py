from django.contrib import admin

from enrollments.models import CourseProgress, Enrollment, LessonProgress


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "status", "enrolled_at", "completed_at")
    list_filter = ("status",)
    search_fields = ("student__username", "course__title")


admin.site.register(LessonProgress)
admin.site.register(CourseProgress)
