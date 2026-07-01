from django import forms

from organizations.models import OrganizationLearner


class OrganizationLearnerForm(forms.ModelForm):
    learner_email = forms.EmailField(help_text="The learner must already have an Acadeval account.")

    class Meta:
        model = OrganizationLearner
        fields = ["learner_email", "department", "active"]
