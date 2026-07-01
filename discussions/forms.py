from django import forms

from discussions.models import Discussion, DiscussionReply, DiscussionReport


class DiscussionForm(forms.ModelForm):
    class Meta:
        model = Discussion
        fields = ["lesson", "title", "body"]
        widgets = {
            "lesson": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
        }


class DiscussionReplyForm(forms.ModelForm):
    class Meta:
        model = DiscussionReply
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"class": "form-control", "rows": 4})}


class DiscussionReportForm(forms.ModelForm):
    class Meta:
        model = DiscussionReport
        fields = ["reason"]
        widgets = {"reason": forms.TextInput(attrs={"class": "form-control", "maxlength": 220})}