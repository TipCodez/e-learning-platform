import csv

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Avg, Count, Max
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from accounts.tokens import send_password_setup_email
from assessments.models import AssignmentSubmission, QuizAttempt
from courses.models import Course
from enrollments.models import CourseProgress, Enrollment, LessonProgress
from organizations.forms import BulkLearnerUploadForm, OrganizationEnrollmentForm, OrganizationLearnerForm
from organizations.models import OrganizationEnrollment, OrganizationLearner, OrganizationReport


User = get_user_model()


def _require_org(user):
    return user.is_organization or user.is_platform_admin


def _unique_username(email):
    base = slugify(email.split("@")[0]) or "learner"
    username = base
    counter = 2
    while User.objects.filter(username=username).exists():
        username = f"{base}{counter}"
        counter += 1
    return username


def _organization_records(user):
    return OrganizationLearner.objects.select_related("learner").filter(organization=user)


def _learner_ids(user):
    return list(_organization_records(user).values_list("learner_id", flat=True))


def _learner_performance_rows(user):
    records = list(_organization_records(user))
    learner_ids = [record.learner_id for record in records]
    enrollments = Enrollment.objects.select_related("course", "progress").filter(student_id__in=learner_ids)
    progress_by_student = {}
    for enrollment in enrollments:
        progress = getattr(enrollment, "progress", None)
        item = progress_by_student.setdefault(
            enrollment.student_id,
            {"enrollments": 0, "completed_courses": 0, "progress_total": 0, "last_accessed_at": None},
        )
        item["enrollments"] += 1
        if enrollment.status == Enrollment.Status.COMPLETED:
            item["completed_courses"] += 1
        item["progress_total"] += progress.percentage if progress else 0
        if enrollment.last_accessed_at and (not item["last_accessed_at"] or enrollment.last_accessed_at > item["last_accessed_at"]):
            item["last_accessed_at"] = enrollment.last_accessed_at

    completed_lessons = dict(
        LessonProgress.objects.filter(enrollment__student_id__in=learner_ids, completed=True)
        .values("enrollment__student_id")
        .annotate(total=Count("id"))
        .values_list("enrollment__student_id", "total")
    )
    quiz_stats = {
        row["student_id"]: row
        for row in QuizAttempt.objects.filter(student_id__in=learner_ids)
        .values("student_id")
        .annotate(attempts=Count("id"), average_score=Avg("score"), passed=Count("id", filter=models.Q(passed=True)))
    }
    assignment_stats = {
        row["student_id"]: row
        for row in AssignmentSubmission.objects.filter(student_id__in=learner_ids)
        .values("student_id")
        .annotate(submissions=Count("id"), graded=Count("id", filter=models.Q(score__isnull=False)), average_score=Avg("score"), last_submitted=Max("submitted_at"))
    }

    rows = []
    for record in records:
        progress = progress_by_student.get(record.learner_id, {"enrollments": 0, "completed_courses": 0, "progress_total": 0, "last_accessed_at": None})
        quiz = quiz_stats.get(record.learner_id, {})
        assignment = assignment_stats.get(record.learner_id, {})
        enrollments_count = progress["enrollments"]
        average_progress = round(progress["progress_total"] / enrollments_count, 1) if enrollments_count else 0
        quiz_attempts = quiz.get("attempts", 0) or 0
        quiz_passed = quiz.get("passed", 0) or 0
        rows.append(
            {
                "record": record,
                "learner": record.learner,
                "enrollments": enrollments_count,
                "completed_courses": progress["completed_courses"],
                "average_progress": average_progress,
                "completed_lessons": completed_lessons.get(record.learner_id, 0),
                "quiz_attempts": quiz_attempts,
                "quiz_average": round(quiz.get("average_score") or 0, 1),
                "quiz_pass_rate": round((quiz_passed / quiz_attempts) * 100, 1) if quiz_attempts else 0,
                "assignment_submissions": assignment.get("submissions", 0) or 0,
                "graded_assignments": assignment.get("graded", 0) or 0,
                "assignment_average": round(assignment.get("average_score") or 0, 1),
                "last_activity": assignment.get("last_submitted") or progress["last_accessed_at"],
            }
        )
    return rows


def _course_performance_rows(learner_ids):
    rows = []
    enrollments = Enrollment.objects.select_related("course", "progress").filter(student_id__in=learner_ids)
    for course in Course.objects.filter(enrollments__in=enrollments).distinct().order_by("title"):
        course_enrollments = [item for item in enrollments if item.course_id == course.id]
        enrollment_ids = [item.id for item in course_enrollments]
        course_learner_ids = [item.student_id for item in course_enrollments]
        progress_values = [getattr(item, "progress", None).percentage for item in course_enrollments if getattr(item, "progress", None)]
        quiz = QuizAttempt.objects.filter(student_id__in=course_learner_ids, quiz__course=course).aggregate(
            attempts=Count("id"),
            average=Avg("score"),
            passed=Count("id", filter=models.Q(passed=True)),
        )
        assignments = AssignmentSubmission.objects.filter(student_id__in=course_learner_ids, assignment__course=course).aggregate(
            submissions=Count("id"),
            graded=Count("id", filter=models.Q(score__isnull=False)),
            average=Avg("score"),
        )
        lessons_completed = LessonProgress.objects.filter(enrollment_id__in=enrollment_ids, completed=True).count()
        rows.append(
            {
                "course": course,
                "learners": len(course_enrollments),
                "completed": sum(1 for item in course_enrollments if item.status == Enrollment.Status.COMPLETED),
                "average_progress": round(sum(progress_values) / len(progress_values), 1) if progress_values else 0,
                "lessons_completed": lessons_completed,
                "quiz_attempts": quiz["attempts"] or 0,
                "quiz_average": round(quiz["average"] or 0, 1),
                "quiz_pass_rate": round(((quiz["passed"] or 0) / quiz["attempts"]) * 100, 1) if quiz["attempts"] else 0,
                "assignment_submissions": assignments["submissions"] or 0,
                "graded_assignments": assignments["graded"] or 0,
                "assignment_average": round(assignments["average"] or 0, 1),
            }
        )
    return rows


def _learner_detail_context(organization, learner):
    records = _organization_records(organization)
    membership = get_object_or_404(records, learner=learner)
    enrollments = Enrollment.objects.select_related("course", "progress").filter(student=learner).order_by("course__title")
    course_rows = []
    for enrollment in enrollments:
        course = enrollment.course
        lessons_completed = LessonProgress.objects.filter(enrollment=enrollment, completed=True).count()
        quiz_attempts = QuizAttempt.objects.select_related("quiz").filter(student=learner, quiz__course=course).order_by("-started_at")
        assignment_submissions = AssignmentSubmission.objects.select_related("assignment").filter(student=learner, assignment__course=course).order_by("-submitted_at")
        course_rows.append(
            {
                "enrollment": enrollment,
                "course": course,
                "progress": getattr(enrollment, "progress", None),
                "lessons_completed": lessons_completed,
                "quiz_attempts": quiz_attempts,
                "quiz_average": round(quiz_attempts.aggregate(avg=Avg("score"))["avg"] or 0, 1),
                "assignment_submissions": assignment_submissions,
                "assignment_average": round(assignment_submissions.aggregate(avg=Avg("score"))["avg"] or 0, 1),
            }
        )
    return {"membership": membership, "learner": learner, "course_rows": course_rows}


@login_required
def learners(request):
    if not _require_org(request.user):
        messages.error(request, "Organization access required.")
        return redirect("dashboards:home")
    form = OrganizationLearnerForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        learner = User.objects.filter(email__iexact=form.cleaned_data["learner_email"]).first()
        if not learner:
            messages.error(request, "No user exists with that email.")
        else:
            OrganizationLearner.objects.update_or_create(
                organization=request.user,
                learner=learner,
                defaults={"department": form.cleaned_data["department"], "active": form.cleaned_data["active"]},
            )
            messages.success(request, "Learner added.")
            return redirect("organizations:learners")
    records = _organization_records(request.user)
    return render(request, "organizations/learners.html", {"form": form, "records": records})


@login_required
def learner_performance(request, learner_id):
    if not _require_org(request.user):
        messages.error(request, "Organization access required.")
        return redirect("dashboards:home")
    learner = get_object_or_404(User, pk=learner_id)
    return render(request, "organizations/learner_performance.html", _learner_detail_context(request.user, learner))


@login_required
def bulk_learners(request):
    if not _require_org(request.user):
        messages.error(request, "Organization access required.")
        return redirect("dashboards:home")
    form = BulkLearnerUploadForm(request.POST or None, request.FILES or None)
    result = None
    if request.method == "POST" and form.is_valid():
        created_users = 0
        attached = 0
        setup_emails_sent = 0
        for email in form.cleaned_data["emails"]:
            learner = User.objects.filter(email__iexact=email).first()
            if not learner:
                learner = User.objects.create(username=_unique_username(email), email=email, role=User.Role.STUDENT)
                learner.set_unusable_password()
                learner.save(update_fields=["password"])
                created_users += 1
                setup_emails_sent += send_password_setup_email(request, learner, organization=request.user)
            OrganizationLearner.objects.update_or_create(
                organization=request.user,
                learner=learner,
                defaults={"department": form.cleaned_data["department"], "active": form.cleaned_data["active"]},
            )
            attached += 1
        result = {"attached": attached, "created_users": created_users, "setup_emails_sent": setup_emails_sent}
        messages.success(request, f"Processed {attached} learners.")
    return render(request, "organizations/bulk_learners.html", {"form": form, "result": result})


@login_required
def bulk_enroll(request):
    if not _require_org(request.user):
        messages.error(request, "Organization access required.")
        return redirect("dashboards:home")
    form = OrganizationEnrollmentForm(request.POST or None, organization=request.user)
    if request.method == "POST" and form.is_valid():
        course = form.cleaned_data["course"]
        learner_ids = [int(value) for value in form.cleaned_data["learners"]]
        org_enrollment = OrganizationEnrollment.objects.create(organization=request.user, course=course)
        enrolled = 0
        for learner in User.objects.filter(id__in=learner_ids):
            org_enrollment.learners.add(learner)
            enrollment, created = Enrollment.objects.get_or_create(student=learner, course=course)
            CourseProgress.objects.get_or_create(enrollment=enrollment)
            enrolled += 1 if created else 0
        messages.success(request, f"Bulk enrollment complete. {enrolled} new learners enrolled.")
        return redirect("organizations:reports")
    return render(request, "organizations/bulk_enroll.html", {"form": form})


@login_required
def reports(request):
    if not _require_org(request.user):
        messages.error(request, "Organization access required.")
        return redirect("dashboards:home")
    records = _organization_records(request.user)
    learner_ids = _learner_ids(request.user)
    learner_rows = _learner_performance_rows(request.user)
    course_rows = _course_performance_rows(learner_ids)
    enrollments = Enrollment.objects.filter(student_id__in=learner_ids)
    quiz_attempts = QuizAttempt.objects.filter(student_id__in=learner_ids)
    assignment_submissions = AssignmentSubmission.objects.filter(student_id__in=learner_ids)
    summary = {
        "learners": records.count(),
        "active_learners": records.filter(active=True).count(),
        "departments": records.exclude(department="").values("department").distinct().count(),
        "enrollments": enrollments.count(),
        "completed": enrollments.filter(status=Enrollment.Status.COMPLETED).count(),
        "average_progress": round(CourseProgress.objects.filter(enrollment__student_id__in=learner_ids).aggregate(avg=Avg("percentage"))["avg"] or 0, 1),
        "lessons_completed": LessonProgress.objects.filter(enrollment__student_id__in=learner_ids, completed=True).count(),
        "quiz_average": round(quiz_attempts.aggregate(avg=Avg("score"))["avg"] or 0, 1),
        "quiz_attempts": quiz_attempts.count(),
        "assignment_average": round(assignment_submissions.aggregate(avg=Avg("score"))["avg"] or 0, 1),
        "assignment_submissions": assignment_submissions.count(),
    }
    reports_qs = OrganizationReport.objects.filter(organization=request.user).order_by("-generated_at")
    return render(
        request,
        "organizations/reports.html",
        {"summary": summary, "reports": reports_qs, "course_rows": course_rows, "learner_rows": learner_rows},
    )


@login_required
@require_POST
def generate_report(request):
    if not _require_org(request.user):
        messages.error(request, "Organization access required.")
        return redirect("dashboards:home")
    learner_ids = _learner_ids(request.user)
    enrollments = Enrollment.objects.filter(student_id__in=learner_ids)
    quiz_average = QuizAttempt.objects.filter(student_id__in=learner_ids).aggregate(avg=Avg("score"))["avg"] or 0
    assignment_average = AssignmentSubmission.objects.filter(student_id__in=learner_ids).aggregate(avg=Avg("score"))["avg"] or 0
    summary = (
        f"Learners: {len(learner_ids)}\n"
        f"Enrollments: {enrollments.count()}\n"
        f"Completed enrollments: {enrollments.filter(status=Enrollment.Status.COMPLETED).count()}\n"
        f"Lessons completed: {LessonProgress.objects.filter(enrollment__student_id__in=learner_ids, completed=True).count()}\n"
        f"Average quiz score: {round(quiz_average, 1)}\n"
        f"Average assignment score: {round(assignment_average, 1)}\n"
        f"Courses represented: {enrollments.values('course').distinct().count()}"
    )
    OrganizationReport.objects.create(organization=request.user, title="Organization training report", summary=summary)
    messages.success(request, "Organization report generated.")
    return redirect("organizations:reports")


@login_required
def export_report(request):
    if not _require_org(request.user):
        messages.error(request, "Organization access required.")
        return redirect("dashboards:home")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="organization-learner-performance.csv"'
    writer = csv.writer(response)
    writer.writerow([
        "email",
        "department",
        "active",
        "enrollments",
        "completed_courses",
        "average_progress",
        "completed_lessons",
        "quiz_attempts",
        "quiz_average",
        "quiz_pass_rate",
        "assignment_submissions",
        "graded_assignments",
        "assignment_average",
        "last_activity",
    ])
    for row in _learner_performance_rows(request.user):
        writer.writerow([
            row["learner"].email,
            row["record"].department,
            row["record"].active,
            row["enrollments"],
            row["completed_courses"],
            row["average_progress"],
            row["completed_lessons"],
            row["quiz_attempts"],
            row["quiz_average"],
            row["quiz_pass_rate"],
            row["assignment_submissions"],
            row["graded_assignments"],
            row["assignment_average"],
            row["last_activity"] or "",
        ])
    return response
