from django import forms

from assessments.models import AssignmentSubmission


class AssignmentSubmissionForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ["response_text", "file"]
        widgets = {"response_text": forms.Textarea(attrs={"rows": 5})}


class GradeSubmissionForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ["score", "feedback"]
        widgets = {"feedback": forms.Textarea(attrs={"rows": 4})}
