from django import forms

from assessments.models import AssignmentSubmission


class AssignmentSubmissionForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ["response_text", "file"]
        widgets = {"response_text": forms.Textarea(attrs={"class": "form-control", "rows": 5})}


class GradeSubmissionForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ["score", "feedback"]
        widgets = {"feedback": forms.Textarea(attrs={"class": "form-control", "rows": 4}), "score": forms.NumberInput(attrs={"class": "form-control", "min": 0})}

    def clean_score(self):
        score = self.cleaned_data["score"]
        if score is None:
            raise forms.ValidationError("Enter a score.")
        max_score = self.instance.assignment.max_score if self.instance and self.instance.assignment_id else 100
        if score < 0 or score > max_score:
            raise forms.ValidationError(f"Score must be between 0 and {max_score}.")
        return score

    def clean_feedback(self):
        feedback = self.cleaned_data["feedback"].strip()
        if len(feedback) < 10:
            raise forms.ValidationError("Give the learner meaningful feedback of at least 10 characters.")
        return feedback
