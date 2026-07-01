import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from courses.models import Course
from payments.models import Payment, SubscriptionPlan


def pricing(request):
    return render(request, "payments/pricing.html", {"plans": SubscriptionPlan.objects.filter(is_active=True)})


@login_required
def checkout(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == "POST":
        gateway = request.POST.get("gateway", Payment.Gateway.PAYSTACK)
        payment = Payment.objects.create(
            user=request.user,
            course=course,
            amount=course.price,
            gateway=gateway,
            reference=f"ACD-{uuid.uuid4().hex[:12].upper()}",
        )
        messages.info(request, "Payment record created. Gateway integration is ready for provider API keys.")
        return redirect("payments:history")
    return render(request, "payments/checkout.html", {"course": course, "gateways": Payment.Gateway.choices})


@login_required
def history(request):
    return render(request, "payments/history.html", {"payments": request.user.payments.all()})
