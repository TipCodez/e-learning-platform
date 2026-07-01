from django.contrib import admin

from organizations.models import OrganizationEnrollment, OrganizationLearner, OrganizationReport

admin.site.register(OrganizationLearner)
admin.site.register(OrganizationEnrollment)
admin.site.register(OrganizationReport)
