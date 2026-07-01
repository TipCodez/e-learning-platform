from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.text import slugify

from accounts.models import CustomUser


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "autofocus": True,
                "placeholder": "you@example.com",
            }
        ),
    )

    error_messages = {
        "invalid_login": "Please enter a correct email address and password.",
        "inactive": "This account is inactive.",
    }


class RegisterForm(UserCreationForm):
    email = forms.EmailField()
    role = forms.ChoiceField(
        choices=[
            (CustomUser.Role.STUDENT, "Student / Learner"),
            (CustomUser.Role.INSTRUCTOR, "Instructor / Course Creator"),
            (CustomUser.Role.ORGANIZATION, "Organization / Institution"),
        ]
    )
    terms_accepted = forms.BooleanField(
        label="I agree to the Terms and Privacy Policy",
        required=True,
    )

    class Meta:
        model = CustomUser
        fields = [
            "first_name",
            "last_name",
            "email",
            "role",
            "phone_number",
            "country",
            "terms_accepted",
            "password1",
            "password2",
        ]

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def _unique_username(self, email):
        base = slugify(email.split("@")[0]).replace("-", "_") or "learner"
        base = base[:140]
        username = base
        counter = 2
        while CustomUser.objects.filter(username=username).exists():
            suffix = f"_{counter}"
            username = f"{base[:150 - len(suffix)]}{suffix}"
            counter += 1
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.username = self._unique_username(user.email)
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "country",
            "bio",
            "profile_picture",
        ]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4}),
        }
