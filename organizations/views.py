import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from django.utils.text import slugify

from enrollments.models import CourseProgress, Enrollment
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
    records = OrganizationLearner.objects.select_related("learner").filter(organization=request.user)
    return render(request, "organizations/learners.html", {"form": form, "records": records})


@login_required
def bulk_learners(request):
    if not _require_org(request.user):
        messages.error(request, "Organization access required.")
        return redirect("dashboards:home")
    form = BulkLearnerUploadForm(request.POST or None)
    result = None
    if request.method == "POST" and form.is_valid():
        created_users = 0
        attached = 0
        for email in form.cleaned_data["emails"]:
            learner = User.objects.filter(email__iexact=email).first()
            if not learner:
                learner = User.objects.create(username=_unique_username(email), email=email, role=User.Role.STUDENT)
                learner.set_unusable_password()
                learner.save(update_fields=["password"])
                created_users += 1
            OrganizationLearner.objects.update_or_create(
                organization=request.user,
                learner=learner,
                defaults={"department": form.cleaned_data["department"], "active": form.cleaned_data["active"]},
            )
            attached += 1
        result = {"attached": attached, "created_users": created_users}
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
    records = OrganizationLearner.objects.select_related("learner").filter(organization=request.user)
    learner_ids = records.values_list("learner_id", flat=True)
    enrollments = Enrollment.objects.filter(student_id__in=learner_ids)
    summary = {
        "learners": records.count(),
        "active_learners": records.filter(active=True).count(),
        "departments": records.exclude(department="").values("department").distinct().count(),
        "enrollments": enrollments.count(),
        "completed": enrollments.filter(status=Enrollment.Status.COMPLETED).count(),
        "average_progress": round(CourseProgress.objects.filter(enrollment__student_id__in=learner_ids).aggregate(avg=Avg("percentage"))["avg"] or 0, 1),
    }
    reports_qs = OrganizationReport.objects.filter(organization=request.user).order_by("-generated_at")
    return render(request, "organizations/reports.html", {"summary": summary, "reports": reports_qs})


@login_required
@require_POST
def generate_report(request):
    if not _require_org(request.user):
        messages.error(request, "Organization access required.")
        return redirect("dashboards:home")
    learner_ids = OrganizationLearner.objects.filter(organization=request.user).values_list("learner_id", flat=True)
    enrollments = Enrollment.objects.filter(student_id__in=learner_ids)
    summary = (
        f"Learners: {len(list(learner_ids))}\n"
        f"Enrollments: {enrollments.count()}\n"
        f"Completed enrollments: {enrollments.filter(status=Enrollment.Status.COMPLETED).count()}\n"
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
    response["Content-Disposition"] = 'attachment; filename="organization-learners.csv"'
    writer = csv.writer(response)
    writer.writerow(["email", "department", "active", "enrollments", "completed"])
    records = OrganizationLearner.objects.select_related("learner").filter(organization=request.user)
    for record in records:
        enrollments = Enrollment.objects.filter(student=record.learner)
        writer.writerow([record.learner.email, record.department, record.active, enrollments.count(), enrollments.filter(status=Enrollment.Status.COMPLETED).count()])
    return response