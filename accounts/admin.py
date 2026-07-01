from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import CustomUser, InstructorProfile, OrganizationProfile, StudentProfile


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_staff", "email_verified", "created_at")
    list_filter = ("role", "is_staff", "is_active", "email_verified")
    search_fields = ("username", "email", "first_name", "last_name")
    fieldsets = UserAdmin.fieldsets + (
        (
            "Acadeval Profile",
            {
                "fields": (
                    "role",
                    "phone_number",
                    "country",
                    "bio",
                    "profile_picture",
                    "email_verified",
                    "terms_accepted",
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Acadeval Profile",
            {"fields": ("email", "role", "terms_accepted")},
        ),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "career_interest", "points", "level", "daily_goal_minutes")
    search_fields = ("user__username", "user__email", "career_interest")


@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "headline", "verification_status", "created_at")
    list_filter = ("verification_status",)
    search_fields = ("user__username", "user__email", "expertise")


@admin.register(OrganizationProfile)
class OrganizationProfileAdmin(admin.ModelAdmin):
    list_display = ("organization_name", "user", "industry", "learner_capacity", "billing_email")
    search_fields = ("organization_name", "user__email", "industry")
