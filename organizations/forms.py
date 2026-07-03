from django import forms
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from courses.models import Course
from organizations.models import OrganizationLearner


class OrganizationLearnerForm(forms.ModelForm):
    learner_email = forms.EmailField(help_text="The learner must already have an Acadeval account.", widget=forms.EmailInput(attrs={"class": "form-control"}))

    class Meta:
        model = OrganizationLearner
        fields = ["learner_email", "department", "active"]
        widgets = {
            "department": forms.TextInput(attrs={"class": "form-control"}),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class BulkLearnerUploadForm(forms.Form):
    emails = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 7, "placeholder": "one learner email per line"}),
        help_text="Existing users are attached. Missing users are created as learner accounts with unusable passwords.",
    )
    upload = forms.FileField(
        required=False,
        help_text="Optional CSV or text file. Put learner emails in the first column.",
        widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".csv,.txt"}),
    )
    department = forms.CharField(max_length=120, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    active = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))

    def clean_emails(self):
        raw = self.cleaned_data.get("emails", "").replace(",", "\n")
        upload = self.files.get("upload")
        if upload:
            if upload.size > 1024 * 512:
                raise forms.ValidationError("Upload a CSV or text file smaller than 512 KB.")
            try:
                uploaded_text = upload.read().decode("utf-8-sig")
            except UnicodeDecodeError as exc:
                raise forms.ValidationError("Upload must be UTF-8 encoded.") from exc
            raw = f"{raw}\n{uploaded_text.replace(',', '\n')}"
        emails = []
        for line in raw.splitlines():
            email = line.strip().lower()
            if email and email not in emails:
                try:
                    validate_email(email)
                except ValidationError as exc:
                    raise forms.ValidationError(f"Invalid email address: {email}") from exc
                emails.append(email)
        if not emails:
            raise forms.ValidationError("Add at least one learner email or upload a CSV file.")
        if len(emails) > 500:
            raise forms.ValidationError("Process 500 learners or fewer at a time.")
        return emails


class OrganizationEnrollmentForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.filter(status=Course.Status.PUBLISHED), widget=forms.Select(attrs={"class": "form-select"}))
    learners = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, required=True)

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        records = OrganizationLearner.objects.select_related("learner").filter(organization=organization, active=True) if organization else []
        self.fields["learners"].choices = [(record.learner_id, record.learner.email) for record in records]
