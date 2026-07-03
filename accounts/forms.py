from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
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


class RegisterForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "autocomplete": "email", "placeholder": "you@example.com"})
    )
    role = forms.ChoiceField(
        choices=[
            (CustomUser.Role.STUDENT, "Student / Learner"),
            (CustomUser.Role.INSTRUCTOR, "Instructor / Course Creator"),
            (CustomUser.Role.ORGANIZATION, "Organization / Institution"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    terms_accepted = forms.BooleanField(
        label="I agree to the Terms and Privacy Policy",
        required=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Confirm password",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
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
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control", "autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "autocomplete": "family-name"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control", "autocomplete": "tel"}),
            "country": forms.TextInput(attrs={"class": "form-control", "autocomplete": "country-name"}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "The two password fields did not match.")
        if password1:
            validate_password(password1)
        return cleaned_data

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
        user.email = self.cleaned_data["email"].strip().lower()
        user.username = self._unique_username(user.email)
        user.set_password(self.cleaned_data["password1"])
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
