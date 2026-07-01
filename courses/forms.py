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
            "block_type": forms.Select(attrs={"class": "form-select"}),
            "order": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "subtitle": forms.TextInput(attrs={"class": "form-control"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 6}),
            "code_language": forms.TextInput(attrs={"class": "form-control", "placeholder": "python, bash, html"}),
            "image_alt": forms.TextInput(attrs={"class": "form-control"}),
            "table_data": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Header A|Header B\nValue A|Value B",
                }
            ),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {"comment": forms.Textarea(attrs={"rows": 3})}
