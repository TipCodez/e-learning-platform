from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from accounts.models import CustomUser
from organizations.forms import OrganizationLearnerForm
from organizations.models import OrganizationLearner


@login_required
def learners(request):
    if not (request.user.is_organization or request.user.is_platform_admin):
        messages.error(request, "Organization access required.")
        return redirect("dashboards:home")
    form = OrganizationLearnerForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        learner = CustomUser.objects.filter(email=form.cleaned_data["learner_email"]).first()
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
