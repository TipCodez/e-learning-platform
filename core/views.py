from django.shortcuts import render


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
    return simple_page(request, "core/coming_soon.html", "Contact")


def become_instructor(request):
    return simple_page(request, "core/coming_soon.html", "Become an Instructor")


def organization_training(request):
    return simple_page(request, "core/coming_soon.html", "Organization Training")


def blog(request):
    return simple_page(request, "core/coming_soon.html", "Blog")


def help_center(request):
    return simple_page(request, "core/coming_soon.html", "Help Center")


def terms(request):
    return simple_page(request, "core/legal.html", "Terms and Conditions")


def privacy(request):
    return simple_page(request, "core/legal.html", "Privacy Policy")
