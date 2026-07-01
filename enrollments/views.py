from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from courses.models import Course
from enrollments.models import CourseProgress, Enrollment


@login_required
def enroll(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if not course.is_free and not request.user.payments.filter(course=course, status="success").exists():
        messages.warning(request, "This paid course needs payment before enrollment.")
        return redirect("payments:checkout", slug=slug)
    enrollment, created = Enrollment.objects.get_or_create(student=request.user, course=course)
    CourseProgress.objects.get_or_create(enrollment=enrollment)
    messages.success(request, "You are enrolled." if created else "You are already enrolled.")
    return redirect("courses:detail", slug=slug)


@login_required
def my_courses(request):
    enrollments = Enrollment.objects.select_related("course").filter(student=request.user)
    return render(request, "enrollments/my_courses.html", {"enrollments": enrollments})


@login_required
def continue_learning(request):
    enrollments = Enrollment.objects.select_related("course").filter(student=request.user, status=Enrollment.Status.ACTIVE)
    return render(request, "enrollments/continue_learning.html", {"enrollments": enrollments})
