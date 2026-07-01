from django.conf import settings
from django.db import models


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Coupon(models.Model):
    code = models.CharField(max_length=40, unique=True)
    discount_percent = models.PositiveSmallIntegerField(default=0)
    valid_from = models.DateTimeField(blank=True, null=True)
    valid_until = models.DateTimeField(blank=True, null=True)
    usage_limit = models.PositiveIntegerField(default=0)
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code


class Payment(models.Model):
    class Gateway(models.TextChoices):
        PAYSTACK = "paystack", "Paystack"
        FLUTTERWAVE = "flutterwave", "Flutterwave"
        MTN_MOMO = "mtn_momo", "MTN Mobile Money"
        VODAFONE_CASH = "vodafone_cash", "Vodafone Cash"
        AIRTELTIGO = "airteltigo", "AirtelTigo Money"
        CARD = "card", "Card"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")
    course = models.ForeignKey("courses.Course", on_delete=models.SET_NULL, blank=True, null=True, related_name="payments")
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, blank=True, null=True, related_name="payments")
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    gateway = models.CharField(max_length=30, choices=Gateway.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reference = models.CharField(max_length=120, unique=True)
    provider_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.reference


class Invoice(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name="invoice")
    invoice_number = models.CharField(max_length=80, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    billing_name = models.CharField(max_length=180)
    billing_email = models.EmailField()


class InstructorPayout(models.Model):
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payouts")
    course = models.ForeignKey("courses.Course", on_delete=models.SET_NULL, blank=True, null=True)
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2)
    platform_commission = models.DecimalField(max_digits=10, decimal_places=2)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
