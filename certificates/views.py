from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render

from certificates.models import Certificate
from certificates.services import ensure_certificate_assets
from courses.models import Course
from enrollments.models import Enrollment


@login_required
def my_certificates(request):
    certificates = Certificate.objects.select_related("course").filter(student=request.user)
    return render(request, "certificates/my_certificates.html", {"certificates": certificates})


@login_required
def generate_certificate(request, slug):
    course = get_object_or_404(Course, slug=slug)
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
    if enrollment.status != Enrollment.Status.COMPLETED:
        messages.error(request, "Complete the course before downloading a certificate.")
        return redirect("courses:detail", slug=slug)
    certificate, _ = Certificate.objects.get_or_create(
        student=request.user,
        course=course,
        defaults={"instructor_name": course.instructor.get_full_name() or course.instructor.username},
    )
    ensure_certificate_assets(request, certificate)
    messages.success(request, "Certificate is ready.")
    return redirect("certificates:detail", certificate_id=certificate.certificate_id)


def verify(request, certificate_id):
    certificate = get_object_or_404(Certificate.objects.select_related("student", "course"), certificate_id=certificate_id)
    return render(request, "certificates/verify.html", {"certificate": certificate})


@login_required
def certificate_detail(request, certificate_id):
    certificate = get_object_or_404(Certificate, certificate_id=certificate_id, student=request.user)
    ensure_certificate_assets(request, certificate)
    return render(request, "certificates/detail.html", {"certificate": certificate})


@login_required
def download_certificate(request, certificate_id):
    certificate = get_object_or_404(Certificate, certificate_id=certificate_id, student=request.user)
    ensure_certificate_assets(request, certificate)
    if not certificate.pdf_file:
        messages.error(request, "Certificate file is not available yet.")
        return redirect("certificates:detail", certificate_id=certificate.certificate_id)
    return FileResponse(
        certificate.pdf_file.open("rb"),
        as_attachment=True,
        filename=f"acadeval-certificate-{certificate.certificate_id}.pdf",
    )
