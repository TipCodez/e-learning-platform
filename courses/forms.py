from django import forms

from courses.models import Course, Lesson, LessonContentBlock, Module, Review


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            "category",
            "subcategory",
            "title",
            "subtitle",
            "description",
            "learning_outcomes",
            "requirements",
            "target_audience",
            "level",
            "duration",
            "thumbnail",
            "intro_video_url",
            "is_free",
            "price",
            "certificate_available",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "learning_outcomes": forms.Textarea(attrs={"rows": 3}),
            "requirements": forms.Textarea(attrs={"rows": 3}),
            "target_audience": forms.Textarea(attrs={"rows": 3}),
        }


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ["title", "description", "order"]


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ["module", "title", "lesson_type", "content", "video_url", "external_url", "file", "order", "duration_minutes", "is_preview"]
        widgets = {"content": forms.Textarea(attrs={"rows": 6})}


class LessonContentBlockForm(forms.ModelForm):
    class Meta:
        model = LessonContentBlock
        fields = [
            "block_type",
            "order",
            "title",
            "subtitle",
            "body",
            "code_language",
            "image",
            "image_alt",
            "table_data",
        ]
        widgets = {
            "block_type": forms.Select(attrs={"class": "form-select", "data-builder-field": "type"}),
            "order": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "title": forms.TextInput(attrs={"class": "form-control", "data-builder-field": "title"}),
            "subtitle": forms.TextInput(attrs={"class": "form-control", "data-builder-field": "subtitle"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 6, "data-builder-field": "body"}),
            "code_language": forms.TextInput(attrs={"class": "form-control", "placeholder": "python, bash, html"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control", "data-image-preview-input": ""}),
            "image_alt": forms.TextInput(attrs={"class": "form-control"}),
            "table_data": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Header A|Header B\nValue A|Value B",
                    "data-builder-field": "table",
                    "data-table-source": "",
                }
            ),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 5}),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 3, "maxlength": 1200}),
        }

    def clean_rating(self):
        rating = self.cleaned_data["rating"]
        if rating < 1 or rating > 5:
            raise forms.ValidationError("Choose a rating from 1 to 5.")
        return rating

    def clean_comment(self):
        return self.cleaned_data["comment"].strip()
