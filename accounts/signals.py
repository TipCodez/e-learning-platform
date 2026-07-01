from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import CustomUser, InstructorProfile, OrganizationProfile, StudentProfile


@receiver(post_save, sender=CustomUser)
def create_role_profile(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.role == CustomUser.Role.STUDENT:
        StudentProfile.objects.create(user=instance)
    elif instance.role == CustomUser.Role.INSTRUCTOR:
        InstructorProfile.objects.create(user=instance)
    elif instance.role == CustomUser.Role.ORGANIZATION:
        OrganizationProfile.objects.create(
            user=instance,
            organization_name=instance.get_full_name() or instance.username,
            billing_email=instance.email,
        )
