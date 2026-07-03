from django.contrib import admin
from django.utils import timezone

from payments.models import Coupon, InstructorPayout, Invoice, Payment, SubscriptionPlan


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("reference", "user", "amount", "gateway", "status", "created_at")
    list_filter = ("gateway", "status")
    search_fields = ("reference", "user__username", "user__email")


admin.site.register(SubscriptionPlan)
admin.site.register(Coupon)
admin.site.register(Invoice)

@admin.register(InstructorPayout)
class InstructorPayoutAdmin(admin.ModelAdmin):
    list_display = ("instructor", "net_amount", "status", "payout_method", "created_at", "processed_at")
    list_filter = ("status", "payout_method", "created_at")
    search_fields = ("instructor__email", "instructor__username", "payout_account")
    readonly_fields = ("created_at",)
    actions = ["approve_payouts", "mark_paid", "reject_payouts"]

    @admin.action(description="Approve selected payout requests")
    def approve_payouts(self, request, queryset):
        queryset.filter(status=InstructorPayout.Status.REQUESTED).update(status=InstructorPayout.Status.APPROVED, processed_at=timezone.now())

    @admin.action(description="Mark selected payouts paid")
    def mark_paid(self, request, queryset):
        queryset.exclude(status=InstructorPayout.Status.REJECTED).update(status=InstructorPayout.Status.PAID, paid=True, processed_at=timezone.now())

    @admin.action(description="Reject selected payout requests")
    def reject_payouts(self, request, queryset):
        queryset.filter(status=InstructorPayout.Status.REQUESTED).update(status=InstructorPayout.Status.REJECTED, processed_at=timezone.now())
