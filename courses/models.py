from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from acadeval.validators import validate_document_upload, validate_image_upload


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=60, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class SubCategory(TimeStampedModel):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["category__name", "name"]
        unique_together = ("category", "slug")
        verbose_name_plural = "subcategories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category} / {self.name}"


class Course(TimeStampedModel):
    class Level(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending Approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        PUBLISHED = "published", "Published"

    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="courses")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="courses")
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="courses")
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=210, unique=True, blank=True)
    subtitle = models.CharField(max_length=220, blank=True)
    description = models.TextField()
    learning_outcomes = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    target_audience = models.TextField(blank=True)
    level = models.CharField(max_length=20, choices=Level.choices, default=Level.BEGINNER)
    duration = models.CharField(max_length=80, blank=True)
    thumbnail = models.ImageField(upload_to="course-thumbnails/", blank=True, null=True, validators=[validate_image_upload])
    intro_video_url = models.URLField(blank=True)
    is_free = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    certificate_available = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    popular = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    rejection_reason = models.TextField(blank=True)
    approved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "featured"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["is_free", "level"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            slug = base
            counter = 2
            while Course.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("courses:detail", kwargs={"slug": self.slug})

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED

    @property
    def average_rating(self):
        aggregate = self.reviews.aggregate(models.Avg("rating"))
        return aggregate["rating__avg"] or 0


class Module(TimeStampedModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "created_at"]
        unique_together = ("course", "order")

    def __str__(self):
        return f"{self.course}: {self.title}"


class Lesson(TimeStampedModel):
    class LessonType(models.TextChoices):
        VIDEO = "video", "Video"
        TEXT = "text", "Text"
        PDF = "pdf", "PDF"
        LINK = "link", "External Link"

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=210, blank=True)
    lesson_type = models.CharField(max_length=20, choices=LessonType.choices, default=LessonType.TEXT)
    content = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    external_url = models.URLField(blank=True)
    file = models.FileField(upload_to="lesson-files/", blank=True, null=True, validators=[validate_document_upload])
    order = models.PositiveIntegerField(default=1)
    duration_minutes = models.PositiveIntegerField(default=0)
    is_preview = models.BooleanField(default=False)

    class Meta:
        ordering = ["module__order", "order"]
        unique_together = ("module", "slug")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title



class LessonContentBlock(TimeStampedModel):
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

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="content_blocks")
    block_type = models.CharField(max_length=30, choices=BlockType.choices, default=BlockType.PARAGRAPH)
    order = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=180, blank=True)
    subtitle = models.CharField(max_length=220, blank=True)
    body = models.TextField(blank=True)
    code_language = models.CharField(max_length=40, blank=True)
    image = models.ImageField(upload_to="lesson-blocks/", blank=True, null=True, validators=[validate_image_upload])
    image_alt = models.CharField(max_length=180, blank=True)
    table_data = models.TextField(
        blank=True,
        help_text="Use one row per line and separate columns with |. The first row is rendered as the table header.",
    )

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.lesson}: {self.get_block_type_display()} #{self.order}"

    @property
    def table_rows(self):
        rows = []
        for line in self.table_data.splitlines():
            cells = [cell.strip() for cell in line.split("|")]
            if any(cells):
                rows.append(cells)
        return rows

class LessonResource(TimeStampedModel):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="resources")
    title = models.CharField(max_length=160)
    file = models.FileField(upload_to="lesson-resources/", blank=True, null=True, validators=[validate_document_upload])
    external_url = models.URLField(blank=True)
    is_downloadable = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Review(TimeStampedModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="course_reviews")
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(blank=True)
    is_approved = models.BooleanField(default=True)

    class Meta:
        unique_together = ("course", "user")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.course} rating {self.rating}"


class WishlistItem(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist_items")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="wishlisted_by")

    class Meta:
        unique_together = ("user", "course")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} saved {self.course}"


class LessonNote(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_notes")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="notes")
    note = models.TextField(blank=True)
    is_bookmarked = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "lesson")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user} note for {self.lesson}"

