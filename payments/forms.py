from django import forms

from payments.models import InstructorPayout, Payment


class CheckoutForm(forms.Form):
    gateway = forms.ChoiceField(
        choices=Payment.Gateway.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    coupon_code = forms.CharField(
        max_length=40,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off", "placeholder": "Optional"}),
    )

    def clean_coupon_code(self):
        return self.cleaned_data["coupon_code"].strip().upper()


class InstructorPayoutRequestForm(forms.ModelForm):
    payout_method = forms.CharField(
        max_length=80,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Bank transfer, Mobile Money, PayPal"}),
    )
    payout_account = forms.CharField(
        max_length=180,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Account number or wallet reference"}),
    )

    class Meta:
        model = InstructorPayout
        fields = ["payout_method", "payout_account", "requested_note"]
        widgets = {
            "requested_note": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Optional note for admins"}),
        }

    def clean_payout_method(self):
        return self.cleaned_data["payout_method"].strip()

    def clean_payout_account(self):
        return self.cleaned_data["payout_account"].strip()
