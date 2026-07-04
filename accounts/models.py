from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from acadeval.validators import validate_image_upload


class CustomUserManager(UserManager):
    def _unique_username(self, email):
        base = slugify(email.split("@")[0]).replace("-", "_") or "user"
        base = base[:140]
        username = base
        counter = 2
        while self.model.objects.filter(username=username).exists():
            suffix = f"_{counter}"
            username = f"{base[:150 - len(suffix)]}{suffix}"
            counter += 1
        return username

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The email address must be set")
        email = self.normalize_email(email)
        extra_fields.setdefault("username", self._unique_username(email))
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", CustomUser.Role.ADMIN)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "student", "Student / Learner"
        INSTRUCTOR = "instructor", "Instructor / Course Creator"
        ORGANIZATION = "organization", "Organization / Institution"
        ADMIN = "admin", "Admin"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    phone_number = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=80, blank=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True, validators=[validate_image_upload])
    email_verified = models.BooleanField(default=False)
    terms_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    class Meta:
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_instructor(self):
        return self.role == self.Role.INSTRUCTOR

    @property
    def is_organization(self):
        return self.role == self.Role.ORGANIZATION

    @property
    def is_platform_admin(self):
        return self.role == self.Role.ADMIN or self.is_staff

    def get_dashboard_url(self):
        if self.is_platform_admin:
            return reverse("dashboards:admin")
        return reverse(f"dashboards:{self.role}")


class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="student_profile")
    learning_goal = models.CharField(max_length=180, blank=True)
    career_interest = models.CharField(max_length=120, blank=True)
    points = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    daily_goal_minutes = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Student profile: {self.user}"


class InstructorProfile(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="instructor_profile")
    headline = models.CharField(max_length=160, blank=True)
    expertise = models.CharField(max_length=220, blank=True)
    website = models.URLField(blank=True)
    verification_status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    payout_name = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Instructor profile: {self.user}"


class OrganizationProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="organization_profile")
    organization_name = models.CharField(max_length=180)
    industry = models.CharField(max_length=120, blank=True)
    website = models.URLField(blank=True)
    learner_capacity = models.PositiveIntegerField(default=0)
    billing_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.organization_name

