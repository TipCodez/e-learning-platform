from decimal import Decimal, ROUND_HALF_UP
import uuid

from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone

from enrollments.models import CourseProgress, Enrollment
from notifications.models import Notification
from payments.models import Coupon, Invoice, Payment


class CouponError(ValueError):
    pass


def build_payment_reference():
    return f"ACD-{uuid.uuid4().hex[:12].upper()}"


def build_invoice_number(payment):
    return f"INV-{payment.created_at:%Y%m%d}-{payment.pk:06d}"


def validate_coupon(code, now=None, lock=False):
    if not code:
        return None

    now = now or timezone.now()
    coupons = Coupon.objects.select_for_update() if lock else Coupon.objects
    coupon = coupons.filter(code__iexact=code.strip(), is_active=True).first()
    if not coupon:
        raise CouponError("Coupon code is invalid.")
    if coupon.valid_from and coupon.valid_from > now:
        raise CouponError("Coupon code is not active yet.")
    if coupon.valid_until and coupon.valid_until < now:
        raise CouponError("Coupon code has expired.")
    if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
        raise CouponError("Coupon usage limit has been reached.")
    if coupon.discount_percent > 100:
        raise CouponError("Coupon discount is not valid.")
    return coupon


def discounted_amount(amount, coupon):
    if not coupon:
        return amount
    discount = (amount * Decimal(coupon.discount_percent) / Decimal("100")).quantize(Decimal("0.01"), ROUND_HALF_UP)
    return max(Decimal("0.00"), amount - discount)


@transaction.atomic
def create_course_payment(user, course, gateway, coupon_code=""):
    coupon = validate_coupon(coupon_code, lock=True)
    amount = discounted_amount(course.price, coupon)
    return Payment.objects.create(
        user=user,
        course=course,
        coupon=coupon,
        amount=amount,
        gateway=gateway,
        reference=build_payment_reference(),
        provider_response={
            "mode": "demo",
            "original_amount": str(course.price),
            "coupon_code": coupon.code if coupon else "",
        },
    )


@transaction.atomic
def confirm_course_payment(payment):
    payment = Payment.objects.select_for_update().select_related("course", "user", "coupon").get(pk=payment.pk)
    if payment.status == Payment.Status.SUCCESS:
        return payment
    if payment.status != Payment.Status.PENDING:
        raise ValueError("Only pending payments can be confirmed.")
    if payment.coupon_id:
        validate_coupon(payment.coupon.code, lock=True)

    payment.status = Payment.Status.SUCCESS
    payment.paid_at = timezone.now()
    payment.provider_response = {
        **payment.provider_response,
        "confirmed_at": payment.paid_at.isoformat(),
        "confirmation": "local_demo",
    }
    payment.save(update_fields=["status", "paid_at", "provider_response"])

    if payment.coupon_id:
        Coupon.objects.filter(pk=payment.coupon_id).update(used_count=models.F("used_count") + 1)

    if payment.course_id:
        enrollment, _ = Enrollment.objects.get_or_create(student=payment.user, course=payment.course)
        CourseProgress.objects.get_or_create(enrollment=enrollment)

    invoice, _ = Invoice.objects.get_or_create(
        payment=payment,
        defaults={
            "invoice_number": build_invoice_number(payment),
            "billing_name": payment.user.get_full_name() or payment.user.email,
            "billing_email": payment.user.email,
        },
    )
    Notification.objects.get_or_create(
        user=payment.user,
        title="Payment confirmed",
        notification_type=Notification.Type.PAYMENT,
        link=reverse("payments:invoice", kwargs={"invoice_number": invoice.invoice_number}),
        defaults={"message": f"Your payment for {payment.course.title if payment.course else 'your subscription'} was successful."},
    )
    return payment
