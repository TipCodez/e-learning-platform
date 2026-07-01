from django import forms

from career.models import CVDocument, CareerProfile, CoverLetter, InterviewPreparation, SkillAssessment


class CareerProfileForm(forms.ModelForm):
    class Meta:
        model = CareerProfile
        fields = ["target_role", "skills", "experience_summary", "portfolio_url", "job_readiness_score"]
        widgets = {
            "skills": forms.Textarea(attrs={"rows": 4}),
            "experience_summary": forms.Textarea(attrs={"rows": 4}),
        }


class CVDocumentForm(forms.ModelForm):
    class Meta:
        model = CVDocument
        fields = ["title", "content"]
        widgets = {"content": forms.Textarea(attrs={"rows": 8})}


class CoverLetterForm(forms.ModelForm):
    class Meta:
        model = CoverLetter
        fields = ["job_title", "company", "content"]
        widgets = {"content": forms.Textarea(attrs={"rows": 8})}


class SkillAssessmentForm(forms.ModelForm):
    class Meta:
        model = SkillAssessment
        fields = ["skill", "score", "recommendation"]
        widgets = {"recommendation": forms.Textarea(attrs={"rows": 4})}


class InterviewPreparationForm(forms.ModelForm):
    class Meta:
        model = InterviewPreparation
        fields = ["target_role", "notes", "checklist_complete"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 5})}
