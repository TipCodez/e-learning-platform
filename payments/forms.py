from django import forms

from payments.models import Payment


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
