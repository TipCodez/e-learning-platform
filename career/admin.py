from django.contrib import admin

from career.models import CVDocument, CareerProfile, CoverLetter, InterviewPreparation, SkillAssessment

admin.site.register(CareerProfile)
admin.site.register(CVDocument)
admin.site.register(CoverLetter)
admin.site.register(SkillAssessment)
admin.site.register(InterviewPreparation)
