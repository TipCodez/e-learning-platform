from django.contrib import admin

from certificates.models import Certificate, CertificateTemplate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("certificate_id", "student", "course", "issue_date", "is_revoked")
    list_filter = ("is_revoked", "issue_date")
    search_fields = ("certificate_id", "student__username", "course__title")


admin.site.register(CertificateTemplate)
