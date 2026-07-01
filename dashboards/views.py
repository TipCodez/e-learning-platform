from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from accounts.models import CustomUser


@login_required
def dashboard_home(request):
    return redirect(request.user.get_dashboard_url())


def _require_role(user, *roles):
    if user.role not in roles and not user.is_staff:
        raise PermissionDenied


@login_required
def student_dashboard(request):
    _require_role(request.user, CustomUser.Role.STUDENT)
    metrics = [
        ("Courses in progress", "0"),
        ("Certificates earned", "0"),
        ("Learning points", getattr(request.user.student_profile, "points", 0) if hasattr(request.user, "student_profile") else 0),
        ("Current streak", "0 days"),
    ]
    return render(request, "dashboards/student.html", {"metrics": metrics})


@login_required
def instructor_dashboard(request):
    _require_role(request.user, CustomUser.Role.INSTRUCTOR)
    metrics = [
        ("Published courses", "0"),
        ("Pending approval", "0"),
        ("Enrolled learners", "0"),
        ("Revenue", "GHS 0"),
    ]
    return render(request, "dashboards/instructor.html", {"metrics": metrics})


@login_required
def organization_dashboard(request):
    _require_role(request.user, CustomUser.Role.ORGANIZATION)
    metrics = [
        ("Learners", "0"),
        ("Active enrollments", "0"),
        ("Certificates", "0"),
        ("Departments", "0"),
    ]
    return render(request, "dashboards/organization.html", {"metrics": metrics})


@login_required
def admin_dashboard(request):
    _require_role(request.user, CustomUser.Role.ADMIN)
    metrics = [
        ("Total users", "0"),
        ("Pending courses", "0"),
        ("Payments", "GHS 0"),
        ("Certificates", "0"),
    ]
    return render(request, "dashboards/admin.html", {"metrics": metrics})
