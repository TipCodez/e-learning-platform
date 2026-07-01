from django import forms
from django.contrib.auth.forms import UserCreationForm

from accounts.models import CustomUser


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
            "username",
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
