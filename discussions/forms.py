from django import forms

from discussions.models import Discussion, DiscussionReply


class DiscussionForm(forms.ModelForm):
    class Meta:
        model = Discussion
        fields = ["course", "lesson", "title", "body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 5})}


class DiscussionReplyForm(forms.ModelForm):
    class Meta:
        model = DiscussionReply
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 4})}
