from django import forms

from core.models import BlogContentBlock, BlogPost, SupportTicket


class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ["title", "excerpt", "content", "author", "is_published"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "excerpt": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "author": forms.Select(attrs={"class": "form-select"}),
            "is_published": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class BlogContentBlockForm(forms.ModelForm):
    class Meta:
        model = BlogContentBlock
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


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ["name", "email", "subject", "message", "priority"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 5}),
        }
