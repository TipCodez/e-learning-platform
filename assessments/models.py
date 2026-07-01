from django.conf import settings
from django.db import models


class Quiz(models.Model):
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="quizzes")
    lesson = models.ForeignKey("courses.Lesson", on_delete=models.SET_NULL, blank=True, null=True, related_name="quizzes")
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    time_limit_minutes = models.PositiveIntegerField(default=0)
    pass_mark = models.PositiveSmallIntegerField(default=70)
    retake_limit = models.PositiveIntegerField(default=3)
    is_final_exam = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    class QuestionType(models.TextChoices):
        MULTIPLE_CHOICE = "multiple_choice", "Multiple Choice"
        TRUE_FALSE = "true_false", "True or False"
        SHORT_ANSWER = "short_answer", "Short Answer"

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    question_type = models.CharField(max_length=30, choices=QuestionType.choices, default=QuestionType.MULTIPLE_CHOICE)
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.text[:80]


class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts")
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    passed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-started_at"]


class QuizResponse(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="responses")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(AnswerOption, on_delete=models.SET_NULL, blank=True, null=True)
    short_answer = models.TextField(blank=True)
    is_correct = models.BooleanField(default=False)
    points_awarded = models.DecimalField(max_digits=5, decimal_places=2, default=0)


class Assignment(models.Model):
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="assignments")
    lesson = models.ForeignKey("courses.Lesson", on_delete=models.SET_NULL, blank=True, null=True, related_name="assignments")
    title = models.CharField(max_length=180)
    instructions = models.TextField()
    due_at = models.DateTimeField(blank=True, null=True)
    max_score = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assignment_submissions")
    file = models.FileField(upload_to="assignment-submissions/", blank=True, null=True)
    response_text = models.TextField(blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="graded_submissions")
    submitted_at = models.DateTimeField(auto_now_add=True)
    graded_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ("assignment", "student")
