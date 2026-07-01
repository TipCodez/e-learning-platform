from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.shortcuts import redirect, render

from accounts.models import CustomUser
from certificates.models import Certificate
from courses.models import Course
from enrollments.models import Enrollment
from organizations.models import OrganizationLearner
from payments.models import Payment


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
    metrics = [
        ("Courses in progress", active_enrollments),
        ("Certificates earned", certificates),
        ("Learning points", getattr(request.user.student_profile, "points", 0) if hasattr(request.user, "student_profile") else 0),
        ("Current streak", "0 days"),
    ]
    return render(request, "dashboards/student.html", {"metrics": metrics})


@login_required
def instructor_dashboard(request):
    _require_role(request.user, CustomUser.Role.INSTRUCTOR)
    courses = Course.objects.filter(instructor=request.user)
    student_count = Enrollment.objects.filter(course__instructor=request.user).values("student").distinct().count()
    revenue = Payment.objects.filter(course__instructor=request.user, status=Payment.Status.SUCCESS).aggregate(total=Sum("amount"))["total"] or 0
    metrics = [
        ("Published courses", courses.filter(status=Course.Status.PUBLISHED).count()),
        ("Pending approval", courses.filter(status=Course.Status.PENDING).count()),
        ("Enrolled learners", student_count),
        ("Revenue", f"GHS {revenue}"),
    ]
    return render(request, "dashboards/instructor.html", {"metrics": metrics})


@login_required
def organization_dashboard(request):
    _require_role(request.user, CustomUser.Role.ORGANIZATION)
    learners = OrganizationLearner.objects.filter(organization=request.user)
    metrics = [
        ("Learners", learners.count()),
        ("Active enrollments", "0"),
        ("Certificates", "0"),
        ("Departments", learners.exclude(department="").values("department").distinct().count()),
    ]
    return render(request, "dashboards/organization.html", {"metrics": metrics})


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
    return render(request, "dashboards/admin.html", {"metrics": metrics})
