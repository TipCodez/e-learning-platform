from django import forms

from core.models import SupportTicket


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ["name", "email", "subject", "message", "priority"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 5}),
        }
