from django.contrib import admin

from assessments.models import AnswerOption, Assignment, AssignmentSubmission, Question, Quiz, QuizAttempt, QuizResponse


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 2


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("quiz", "question_type", "order", "points")
    inlines = [AnswerOptionInline]


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "pass_mark", "retake_limit", "is_final_exam")
    list_filter = ("is_final_exam",)


admin.site.register(QuizAttempt)
admin.site.register(QuizResponse)
admin.site.register(Assignment)
admin.site.register(AssignmentSubmission)
