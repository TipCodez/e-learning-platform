from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from core.forms import SupportTicketForm
from core.models import BlogPost, FAQ


def home(request):
    featured_courses = [
        {
            "title": "Python Fundamentals",
            "level": "Beginner",
            "duration": "6 weeks",
            "price": "Free",
        },
        {
            "title": "Digital Marketing Essentials",
            "level": "Intermediate",
            "duration": "4 weeks",
            "price": "GHS 120",
        },
        {
            "title": "Career-Ready Web Development",
            "level": "Beginner",
            "duration": "10 weeks",
            "price": "GHS 250",
        },
    ]
    stats = [
        ("12k+", "learners"),
        ("180+", "courses planned"),
        ("94%", "completion satisfaction"),
        ("35+", "career paths"),
    ]
    return render(request, "core/home.html", {"featured_courses": featured_courses, "stats": stats})


def simple_page(request, template_name, title):
    return render(request, template_name, {"title": title})


def courses(request):
    return simple_page(request, "core/coming_soon.html", "Courses")


def categories(request):
    return simple_page(request, "core/coming_soon.html", "Categories")


def learning_paths(request):
    return simple_page(request, "core/coming_soon.html", "Learning Paths")


def certificate_verify(request):
    return simple_page(request, "core/coming_soon.html", "Verify Certificate")


def pricing(request):
    return simple_page(request, "core/coming_soon.html", "Pricing")


def about(request):
    return simple_page(request, "core/coming_soon.html", "About Acadeval")


def contact(request):
    initial = {}
    if request.user.is_authenticated:
        initial = {
            "name": request.user.get_full_name() or request.user.username,
            "email": request.user.email,
        }
    form = SupportTicketForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        ticket = form.save(commit=False)
        if request.user.is_authenticated:
            ticket.user = request.user
        ticket.save()
        messages.success(request, "Your support request has been sent.")
        return redirect("core:contact")
    return render(request, "core/contact.html", {"form": form})


def become_instructor(request):
    return simple_page(request, "core/coming_soon.html", "Become an Instructor")


def organization_training(request):
    return simple_page(request, "core/coming_soon.html", "Organization Training")


def blog(request):
    posts = BlogPost.objects.filter(is_published=True)
    paginator = Paginator(posts, 6)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "core/blog.html", {"page": page})


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    return render(request, "core/blog_detail.html", {"post": post})


def help_center(request):
    faqs = FAQ.objects.filter(is_active=True)
    categories = faqs.exclude(category="").values_list("category", flat=True).distinct()
    return render(request, "core/help_center.html", {"faqs": faqs, "categories": categories})


def terms(request):
    return simple_page(request, "core/legal.html", "Terms and Conditions")


def privacy(request):
    return simple_page(request, "core/legal.html", "Privacy Policy")
