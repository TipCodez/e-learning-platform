from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from assessments.forms import AssignmentSubmissionForm, GradeSubmissionForm
from assessments.models import AnswerOption, Assignment, AssignmentSubmission, Quiz, QuizAttempt, QuizResponse
from enrollments.models import Enrollment
from gamification.services import record_quiz_passed
from notifications.models import Notification
from notifications.services import notify_user


def _can_access_course(user, course):
    return (
        course.instructor == user
        or user.is_platform_admin
        or Enrollment.objects.filter(student=user, course=course).exists()
    )


@login_required
def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz.objects.select_related("course", "course__instructor").prefetch_related("questions__options"), pk=quiz_id)
    if not _can_access_course(request.user, quiz.course):
        messages.error(request, "Enroll before taking this quiz.")
        return redirect("courses:detail", slug=quiz.course.slug)
    attempts_count = QuizAttempt.objects.filter(quiz=quiz, student=request.user).count()
    if request.method == "POST" and quiz.retake_limit and attempts_count >= quiz.retake_limit:
        messages.error(request, "You have reached the retake limit for this quiz.")
        return redirect("assessments:quiz", quiz_id=quiz.id)
    if request.method == "POST":
        attempt = QuizAttempt.objects.create(quiz=quiz, student=request.user)
        total_points = sum(q.points for q in quiz.questions.all()) or 1
        earned = 0
        for question in quiz.questions.all():
            option_id = request.POST.get(f"question_{question.id}")
            selected = AnswerOption.objects.filter(pk=option_id, question=question).first() if option_id else None
            is_correct = bool(selected and selected.is_correct)
            points = question.points if is_correct else 0
            earned += points
            QuizResponse.objects.create(attempt=attempt, question=question, selected_option=selected, is_correct=is_correct, points_awarded=points)
        attempt.score = round((earned / total_points) * 100, 2)
        attempt.passed = attempt.score >= quiz.pass_mark
        attempt.submitted_at = timezone.now()
        attempt.save()
        if attempt.passed:
            record_quiz_passed(request.user, quiz)
        messages.success(request, f"Quiz submitted. Score: {attempt.score}%.")
        return redirect("assessments:quiz_result", attempt_id=attempt.id)
    return render(request, "assessments/quiz_detail.html", {"quiz": quiz, "attempts_count": attempts_count})


@login_required
def quiz_result(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, pk=attempt_id, student=request.user)
    return render(request, "assessments/quiz_result.html", {"attempt": attempt})


@login_required
def assignment_detail(request, assignment_id):
    assignment = get_object_or_404(Assignment.objects.select_related("course", "course__instructor"), pk=assignment_id)
    if not _can_access_course(request.user, assignment.course):
        messages.error(request, "Enroll before submitting this assignment.")
        return redirect("courses:detail", slug=assignment.course.slug)
    submission = AssignmentSubmission.objects.filter(assignment=assignment, student=request.user).first()
    if request.method == "POST":
        form = AssignmentSubmissionForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.assignment = assignment
            submission.student = request.user
            submission.save()
            notify_user(
                assignment.course.instructor,
                title="Assignment submitted",
                message=f"{request.user.email} submitted {assignment.title}.",
                notification_type=Notification.Type.ASSIGNMENT_FEEDBACK,
                link=reverse("assessments:grade_submission", kwargs={"submission_id": submission.id}),
            )
            messages.success(request, "Assignment submitted.")
            return redirect("assessments:assignment", assignment_id=assignment.id)
    else:
        form = AssignmentSubmissionForm(instance=submission)
    return render(request, "assessments/assignment_detail.html", {"assignment": assignment, "form": form, "submission": submission})


@login_required
def submission_queue(request):
    if not (request.user.is_instructor or request.user.is_platform_admin):
        messages.error(request, "Instructor access required.")
        return redirect("dashboards:home")
    submissions = AssignmentSubmission.objects.select_related("assignment", "assignment__course", "student")
    status = request.GET.get("status", "pending")
    if not request.user.is_platform_admin:
        submissions = submissions.filter(assignment__course__instructor=request.user)
    if status == "graded":
        submissions = submissions.filter(score__isnull=False)
    elif status == "all":
        pass
    else:
        submissions = submissions.filter(score__isnull=True)
    return render(request, "assessments/submission_queue.html", {"submissions": submissions, "status": status})


@login_required
def grade_submission(request, submission_id):
    submission = get_object_or_404(AssignmentSubmission.objects.select_related("assignment", "assignment__course", "student"), pk=submission_id)
    if submission.assignment.course.instructor != request.user and not request.user.is_platform_admin:
        messages.error(request, "Only the instructor can grade this submission.")
        return redirect("dashboards:home")
    form = GradeSubmissionForm(request.POST or None, instance=submission)
    if request.method == "POST" and form.is_valid():
        graded = form.save(commit=False)
        graded.graded_by = request.user
        graded.graded_at = timezone.now()
        graded.save()
        notify_user(
            graded.student,
            title="Assignment graded",
            message=f"Your submission for {graded.assignment.title} was graded.",
            notification_type=Notification.Type.ASSIGNMENT_FEEDBACK,
            link=reverse("assessments:assignment", kwargs={"assignment_id": graded.assignment_id}),
        )
        messages.success(request, "Submission graded.")
        return redirect("assessments:submissions")
    return render(request, "assessments/grade_submission.html", {"form": form, "submission": submission})
