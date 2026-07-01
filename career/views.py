from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from career.forms import CVDocumentForm, CareerProfileForm, CoverLetterForm, InterviewPreparationForm, SkillAssessmentForm
from career.models import CVDocument, CareerProfile, CoverLetter, InterviewPreparation, SkillAssessment


@login_required
def career_dashboard(request):
    profile, _ = CareerProfile.objects.get_or_create(user=request.user)
    return render(request, "career/dashboard.html", {"profile": profile})


@login_required
def profile(request):
    profile, _ = CareerProfile.objects.get_or_create(user=request.user)
    form = CareerProfileForm(request.POST or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Career profile updated.")
        return redirect("career:dashboard")
    return render(request, "career/form.html", {"form": form, "title": "Career Profile"})


def _create_owned_record(request, form_class, template_title):
    form = form_class(request.POST or None)
    if request.method == "POST" and form.is_valid():
        record = form.save(commit=False)
        record.user = request.user
        record.save()
        messages.success(request, f"{template_title} saved.")
        return redirect("career:dashboard")
    return render(request, "career/form.html", {"form": form, "title": template_title})


@login_required
def cv_builder(request):
    return _create_owned_record(request, CVDocumentForm, "CV Builder")


@login_required
def cover_letter(request):
    return _create_owned_record(request, CoverLetterForm, "Cover Letter")


@login_required
def skill_assessment(request):
    return _create_owned_record(request, SkillAssessmentForm, "Skill Assessment")


@login_required
def interview_prep(request):
    return _create_owned_record(request, InterviewPreparationForm, "Interview Preparation")
