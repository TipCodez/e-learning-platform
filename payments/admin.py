from django.contrib import admin

from payments.models import Coupon, InstructorPayout, Invoice, Payment, SubscriptionPlan


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("reference", "user", "amount", "gateway", "status", "created_at")
    list_filter = ("gateway", "status")
    search_fields = ("reference", "user__username", "user__email")


admin.site.register(SubscriptionPlan)
admin.site.register(Coupon)
admin.site.register(Invoice)
admin.site.register(InstructorPayout)
