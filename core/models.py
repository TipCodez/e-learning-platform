from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from acadeval.validators import validate_image_upload


class AIAssistantSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_assistant_sessions")
    course = models.ForeignKey("courses.Course", on_delete=models.SET_NULL, blank=True, null=True)
    prompt = models.TextField()
    response_placeholder = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class BlogPost(models.Model):
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=210, unique=True, blank=True)
    excerpt = models.TextField(blank=True)
    content = models.TextField(blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            slug = base
            counter = 2
            while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("core:blog_detail", kwargs={"slug": self.slug})

    def __str__(self):
        return self.title



class BlogContentBlock(models.Model):
    class BlockType(models.TextChoices):
        PARAGRAPH = "paragraph", "Paragraph"
        SUBTITLE = "subtitle", "Subtitle"
        SECTION = "section", "Section"
        CODE = "code", "Code Fence"
        OUTPUT = "output", "Output"
        SCREENSHOT = "screenshot", "Screenshot"
        TABLE = "table", "Table"
        TILE = "tile", "Tile"
        QUOTE = "quote", "Quote"
        CALLOUT = "callout", "Callout"

    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name="blocks")
    block_type = models.CharField(max_length=30, choices=BlockType.choices, default=BlockType.PARAGRAPH)
    order = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=180, blank=True)
    subtitle = models.CharField(max_length=220, blank=True)
    body = models.TextField(blank=True)
    code_language = models.CharField(max_length=40, blank=True)
    image = models.ImageField(upload_to="blog-blocks/", blank=True, null=True, validators=[validate_image_upload])
    image_alt = models.CharField(max_length=180, blank=True)
    table_data = models.TextField(
        blank=True,
        help_text="Use one row per line and separate columns with |. The first row is rendered as the table header.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.post}: {self.get_block_type_display()} #{self.order}"

    @property
    def table_rows(self):
        rows = []
        for line in self.table_data.splitlines():
            cells = [cell.strip() for cell in line.split("|")]
            if any(cells):
                rows.append(cells)
        return rows

class FAQ(models.Model):
    question = models.CharField(max_length=220)
    answer = models.TextField()
    category = models.CharField(max_length=80, blank=True)
    order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "question"]

    def __str__(self):
        return self.question


class SupportTicket(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In Progress"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="support_tickets")
    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=180)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.subject

