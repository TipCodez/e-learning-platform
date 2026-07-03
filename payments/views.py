from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from courses.models import Course
from payments.forms import CheckoutForm, InstructorPayoutRequestForm
from payments.models import InstructorPayout, Invoice, Payment, SubscriptionPlan
from payments.services import CouponError, confirm_course_payment, create_course_payment, discounted_amount, validate_coupon


def pricing(request):
    return render(request, "payments/pricing.html", {"plans": SubscriptionPlan.objects.filter(is_active=True)})


@login_required
def checkout(request, slug):
    course = get_object_or_404(Course, slug=slug, status=Course.Status.PUBLISHED)
    if course.is_free:
        messages.info(request, "This course is free. You can enroll without checkout.")
        return redirect("enrollments:enroll", slug=course.slug)
    if request.user.payments.filter(course=course, status=Payment.Status.SUCCESS).exists():
        messages.info(request, "You already have a successful payment for this course.")
        return redirect("enrollments:enroll", slug=course.slug)

    preview_amount = course.price
    preview_coupon = None
    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                payment = create_course_payment(
                    user=request.user,
                    course=course,
                    gateway=form.cleaned_data["gateway"],
                    coupon_code=form.cleaned_data["coupon_code"],
                )
            except CouponError as exc:
                form.add_error("coupon_code", str(exc))
            else:
                messages.info(request, "Payment created. Confirm to complete this demo transaction securely.")
                return redirect("payments:success", reference=payment.reference)
    else:
        form = CheckoutForm(initial={"gateway": Payment.Gateway.PAYSTACK})

    coupon_code = request.POST.get("coupon_code", "") if request.method == "POST" else ""
    if coupon_code and not form.errors.get("coupon_code"):
        try:
            preview_coupon = validate_coupon(coupon_code)
            preview_amount = discounted_amount(course.price, preview_coupon)
        except CouponError:
            preview_coupon = None

    return render(
        request,
        "payments/checkout.html",
        {
            "course": course,
            "form": form,
            "preview_amount": preview_amount,
            "preview_coupon": preview_coupon,
        },
    )


@login_required
def success(request, reference):
    payment = get_object_or_404(
        Payment.objects.select_related("course", "coupon", "invoice"),
        reference=reference,
        user=request.user,
    )
    return render(request, "payments/success.html", {"payment": payment})


@login_required
@require_POST
def confirm(request, reference):
    payment = get_object_or_404(Payment, reference=reference, user=request.user)
    if payment.status != Payment.Status.PENDING:
        messages.info(request, "This payment has already been processed.")
        return redirect("payments:success", reference=payment.reference)
    try:
        payment = confirm_course_payment(payment)
    except CouponError as exc:
        messages.error(request, str(exc))
        return redirect("payments:success", reference=payment.reference)
    messages.success(request, "Payment confirmed. You are enrolled and your invoice is ready.")
    return redirect("payments:invoice", invoice_number=payment.invoice.invoice_number)


@login_required
def invoice(request, invoice_number):
    invoice_obj = get_object_or_404(
        Invoice.objects.select_related("payment", "payment__course"),
        invoice_number=invoice_number,
        payment__user=request.user,
    )
    return render(request, "payments/invoice.html", {"invoice": invoice_obj})


@login_required
def invoice_download(request, invoice_number):
    invoice_obj = get_object_or_404(
        Invoice.objects.select_related("payment", "payment__course"),
        invoice_number=invoice_number,
        payment__user=request.user,
    )
    html = render_to_string("payments/invoice_download.html", {"invoice": invoice_obj}, request=request)
    response = HttpResponse(html, content_type="text/html; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{invoice_obj.invoice_number}.html"'
    return response


@login_required
def history(request):
    payments = request.user.payments.select_related("course", "coupon", "invoice")
    return render(request, "payments/history.html", {"payments": payments})


@login_required
@require_POST
def request_instructor_payout(request):
    if not (request.user.is_instructor or request.user.is_platform_admin):
        messages.error(request, "Instructor access required.")
        return redirect("dashboards:home")
    form = InstructorPayoutRequestForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Add a payout method and account before requesting payout.")
        return redirect("dashboards:instructor_earnings")
    successful_payments = Payment.objects.filter(course__instructor=request.user, status=Payment.Status.SUCCESS)
    gross = successful_payments.aggregate(total=Sum("amount"))["total"] or 0
    paid_or_pending = InstructorPayout.objects.filter(
        instructor=request.user,
        status__in=[InstructorPayout.Status.REQUESTED, InstructorPayout.Status.APPROVED, InstructorPayout.Status.PAID],
    ).aggregate(total=Sum("net_amount"))["total"] or 0
    commission_rate = 20
    commission = gross * commission_rate / 100
    available = max(gross - commission - paid_or_pending, 0)
    if available <= 0:
        messages.error(request, "There are no available earnings to request yet.")
        return redirect("dashboards:instructor_earnings")
    payout = form.save(commit=False)
    payout.instructor = request.user
    payout.gross_amount = gross
    payout.platform_commission = commission
    payout.net_amount = available
    payout.status = InstructorPayout.Status.REQUESTED
    payout.save()
    messages.success(request, "Payout request submitted for admin review.")
    return redirect("dashboards:instructor_earnings")
