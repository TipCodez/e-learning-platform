from django import forms

from courses.models import Course, Lesson, Module, Review


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


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {"comment": forms.Textarea(attrs={"rows": 3})}
