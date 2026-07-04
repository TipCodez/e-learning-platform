from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, Sum
from django.shortcuts import redirect, render

from accounts.models import CustomUser
from assessments.models import AssignmentSubmission
from certificates.models import Certificate
from courses.models import Course
from enrollments.models import CourseProgress, Enrollment
from gamification.models import Leaderboard, LearningStreak
from organizations.models import OrganizationEnrollment, OrganizationLearner, OrganizationReport
from payments.forms import InstructorPayoutRequestForm
from payments.models import InstructorPayout, Payment


@login_required
def dashboard_home(request):
    return redirect(request.user.get_dashboard_url())


def _require_role(user, *roles):
    if user.role not in roles and not user.is_staff:
        raise PermissionDenied


@login_required
def student_dashboard(request):
    _require_role(request.user, CustomUser.Role.STUDENT)
    active_enrollments = Enrollment.objects.filter(student=request.user, status=Enrollment.Status.ACTIVE).count()
    certificates = Certificate.objects.filter(student=request.user).count()
    leaderboard = Leaderboard.objects.filter(user=request.user).first()
    streak = LearningStreak.objects.filter(user=request.user).first()
    metrics = [
        ("Courses in progress", active_enrollments),
        ("Certificates earned", certificates),
        ("Learning points", leaderboard.points if leaderboard else 0),
        ("Current streak", f"{streak.current_streak if streak else 0} days"),
    ]
    recent_enrollments = list(
        Enrollment.objects.select_related("course")
        .filter(student=request.user)
        .order_by("-last_accessed_at", "-enrolled_at")[:5]
    )
    progress_map = {
        progress.enrollment_id: progress
        for progress in CourseProgress.objects.filter(enrollment__in=recent_enrollments)
    }
    learning_rows = [
        {
            "enrollment": enrollment,
            "course": enrollment.course,
            "progress": progress_map.get(enrollment.id),
        }
        for enrollment in recent_enrollments
    ]
    recommended_courses = (
        Course.objects.filter(status=Course.Status.PUBLISHED)
        .exclude(enrollments__student=request.user)
        .select_related("category", "instructor")
        .order_by("-featured", "-created_at")[:3]
    )
    return render(
        request,
        "dashboards/student.html",
        {
            "metrics": metrics,
            "learning_rows": learning_rows,
            "recommended_courses": recommended_courses,
        },
    )


@login_required
def instructor_dashboard(request):
    _require_role(request.user, CustomUser.Role.INSTRUCTOR)
    courses = Course.objects.filter(instructor=request.user)
    student_count = Enrollment.objects.filter(course__instructor=request.user).values("student").distinct().count()
    revenue = Payment.objects.filter(course__instructor=request.user, status=Payment.Status.SUCCESS).aggregate(total=Sum("amount"))["total"] or 0
    pending_submissions = AssignmentSubmission.objects.filter(assignment__course__instructor=request.user, score__isnull=True).count()
    metrics = [
        ("Published courses", courses.filter(status=Course.Status.PUBLISHED).count()),
        ("Pending approval", courses.filter(status=Course.Status.PENDING).count()),
        ("Enrolled learners", student_count),
        ("Revenue", f"GHS {revenue}"),
    ]
    recent_courses = courses.select_related("category").annotate(learner_count=Count("enrollments")).order_by("-updated_at")[:5]
    pending_submission_rows = (
        AssignmentSubmission.objects.select_related("assignment", "assignment__course", "student")
        .filter(assignment__course__instructor=request.user, score__isnull=True)
        .order_by("submitted_at")[:5]
    )
    return render(
        request,
        "dashboards/instructor.html",
        {
            "metrics": metrics,
            "pending_submissions": pending_submissions,
            "recent_courses": recent_courses,
            "pending_submission_rows": pending_submission_rows,
        },
    )


@login_required
def instructor_analytics(request):
    _require_role(request.user, CustomUser.Role.INSTRUCTOR)
    courses = Course.objects.filter(instructor=request.user).prefetch_related("enrollments", "certificates", "payments")
    course_rows = []
    for course in courses:
        enrollments = Enrollment.objects.filter(course=course)
        progress = CourseProgress.objects.filter(enrollment__course=course).aggregate(avg=Avg("percentage"))["avg"] or 0
        revenue = Payment.objects.filter(course=course, status=Payment.Status.SUCCESS).aggregate(total=Sum("amount"))["total"] or 0
        course_rows.append(
            {
                "course": course,
                "learners": enrollments.values("student").distinct().count(),
                "completed": enrollments.filter(status=Enrollment.Status.COMPLETED).count(),
                "average_progress": round(progress, 1),
                "certificates": Certificate.objects.filter(course=course).count(),
                "revenue": revenue,
            }
        )
    totals = {
        "courses": courses.count(),
        "learners": Enrollment.objects.filter(course__instructor=request.user).values("student").distinct().count(),
        "completed": Enrollment.objects.filter(course__instructor=request.user, status=Enrollment.Status.COMPLETED).count(),
        "revenue": Payment.objects.filter(course__instructor=request.user, status=Payment.Status.SUCCESS).aggregate(total=Sum("amount"))["total"] or 0,
    }
    return render(request, "dashboards/instructor_analytics.html", {"course_rows": course_rows, "totals": totals})


@login_required
def instructor_earnings(request):
    _require_role(request.user, CustomUser.Role.INSTRUCTOR)
    payments = Payment.objects.select_related("course", "user").filter(course__instructor=request.user, status=Payment.Status.SUCCESS)
    gross = payments.aggregate(total=Sum("amount"))["total"] or 0
    commission_rate = 20
    commission = gross * commission_rate / 100
    net = gross - commission
    payouts = InstructorPayout.objects.filter(instructor=request.user)
    paid_or_pending = payouts.filter(
        status__in=[InstructorPayout.Status.REQUESTED, InstructorPayout.Status.APPROVED, InstructorPayout.Status.PAID]
    ).aggregate(total=Sum("net_amount"))["total"] or 0
    available = max(net - paid_or_pending, 0)
    return render(
        request,
        "dashboards/instructor_earnings.html",
        {
            "payments": payments,
            "gross": gross,
            "commission_rate": commission_rate,
            "commission": commission,
            "net": net,
            "available": available,
            "payouts": payouts,
            "payout_form": InstructorPayoutRequestForm(),
        },
    )


@login_required
def organization_dashboard(request):
    _require_role(request.user, CustomUser.Role.ORGANIZATION)
    learners = OrganizationLearner.objects.filter(organization=request.user, active=True)
    learner_ids = learners.values_list("learner_id", flat=True)
    metrics = [
        ("Learners", learners.count()),
        ("Active enrollments", Enrollment.objects.filter(student_id__in=learner_ids, status=Enrollment.Status.ACTIVE).count()),
        ("Certificates", Certificate.objects.filter(student_id__in=learner_ids).count()),
        ("Departments", learners.exclude(department="").values("department").distinct().count()),
    ]
    recent_learners = learners.select_related("learner").order_by("-added_at")[:5]
    team_enrollments = OrganizationEnrollment.objects.select_related("course").filter(organization=request.user).order_by("-created_at")[:5]
    recent_reports = OrganizationReport.objects.filter(organization=request.user).order_by("-generated_at")[:3]
    return render(
        request,
        "dashboards/organization.html",
        {
            "metrics": metrics,
            "recent_learners": recent_learners,
            "team_enrollments": team_enrollments,
            "recent_reports": recent_reports,
        },
    )


@login_required
def admin_dashboard(request):
    _require_role(request.user, CustomUser.Role.ADMIN)
    revenue = Payment.objects.filter(status=Payment.Status.SUCCESS).aggregate(total=Sum("amount"))["total"] or 0
    metrics = [
        ("Total users", CustomUser.objects.count()),
        ("Pending courses", Course.objects.filter(status=Course.Status.PENDING).count()),
        ("Payments", f"GHS {revenue}"),
        ("Certificates", Certificate.objects.count()),
    ]
    pending_courses = Course.objects.select_related("instructor", "category").filter(status=Course.Status.PENDING).order_by("created_at")[:5]
    recent_users = CustomUser.objects.order_by("-created_at")[:5]
    return render(
        request,
        "dashboards/admin.html",
        {"metrics": metrics, "pending_courses": pending_courses, "recent_users": recent_users},
    )
