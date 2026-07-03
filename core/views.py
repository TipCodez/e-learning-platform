from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.forms import BlogContentBlockForm, SupportTicketForm
from core.models import BlogContentBlock, BlogPost, FAQ
from courses.models import Course


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
    features = [
        ("Bulk learner management", "Add existing learners or create learner accounts from a simple email list."),
        ("Team enrollment", "Enroll selected learners into published courses and keep cohort records."),
        ("Progress reporting", "Review learner counts, enrollments, completion totals, average progress, and export CSV reports."),
        ("Certificates and outcomes", "Track certificates earned by organization learners as courses are completed."),
    ]
    return render(request, "core/organization_training.html", {"features": features})


def blog(request):
    posts = BlogPost.objects.filter(is_published=True)
    paginator = Paginator(posts, 6)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "core/blog.html", {"page": page})


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost.objects.prefetch_related("blocks"), slug=slug, is_published=True)
    return render(request, "core/blog_detail.html", {"post": post})


def _require_platform_admin(request):
    if not request.user.is_authenticated or not request.user.is_platform_admin:
        messages.error(request, "Admin access required.")
        return False
    return True


def manage_blog_blocks(request, slug):
    if not _require_platform_admin(request):
        return redirect("dashboards:home")
    post = get_object_or_404(BlogPost.objects.prefetch_related("blocks"), slug=slug)
    form = BlogContentBlockForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        block = form.save(commit=False)
        block.post = post
        block.save()
        messages.success(request, "Blog content block added.")
        return redirect("core:manage_blog_blocks", slug=post.slug)
    return render(request, "core/manage_blog_blocks.html", {"post": post, "form": form, "builder_kind": "blog"})


def edit_blog_block(request, slug, block_id):
    if not _require_platform_admin(request):
        return redirect("dashboards:home")
    post = get_object_or_404(BlogPost, slug=slug)
    block = get_object_or_404(BlogContentBlock, pk=block_id, post=post)
    form = BlogContentBlockForm(request.POST or None, request.FILES or None, instance=block)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Blog content block updated.")
        return redirect("core:manage_blog_blocks", slug=post.slug)
    return render(request, "core/blog_block_form.html", {"post": post, "block": block, "form": form})


@require_POST
def delete_blog_block(request, slug, block_id):
    if not _require_platform_admin(request):
        return redirect("dashboards:home")
    post = get_object_or_404(BlogPost, slug=slug)
    block = get_object_or_404(BlogContentBlock, pk=block_id, post=post)
    block.delete()
    messages.success(request, "Blog content block deleted.")
    return redirect("core:manage_blog_blocks", slug=post.slug)


@require_POST
def move_blog_block(request, slug, block_id, direction):
    if not _require_platform_admin(request):
        return redirect("dashboards:home")
    post = get_object_or_404(BlogPost, slug=slug)
    block = get_object_or_404(BlogContentBlock, pk=block_id, post=post)
    ordered_blocks = list(post.blocks.order_by("order", "created_at"))
    index = ordered_blocks.index(block)
    swap_with = None
    if direction == "up" and index > 0:
        swap_with = ordered_blocks[index - 1]
    elif direction == "down" and index + 1 < len(ordered_blocks):
        swap_with = ordered_blocks[index + 1]
    if swap_with:
        block.order, swap_with.order = swap_with.order, block.order
        block.save(update_fields=["order", "updated_at"])
        swap_with.save(update_fields=["order", "updated_at"])
        messages.success(request, "Blog block order updated.")
    return redirect("core:manage_blog_blocks", slug=post.slug)


@require_POST
def reorder_blog_blocks(request, slug):
    if not request.user.is_authenticated or not request.user.is_platform_admin:
        return JsonResponse({"ok": False, "error": "Permission denied."}, status=403)
    post = get_object_or_404(BlogPost, slug=slug)
    ordered_ids = request.POST.getlist("block_order")
    blocks = {str(block.id): block for block in post.blocks.filter(id__in=ordered_ids)}
    if len(blocks) != len(ordered_ids):
        return JsonResponse({"ok": False, "error": "Invalid block order."}, status=400)
    for index, block_id in enumerate(ordered_ids, start=1):
        block = blocks[block_id]
        if block.order != index:
            block.order = index
            block.save(update_fields=["order", "updated_at"])
    return JsonResponse({"ok": True})


def help_center(request):
    faqs = FAQ.objects.filter(is_active=True)
    categories = faqs.exclude(category="").values_list("category", flat=True).distinct()
    return render(request, "core/help_center.html", {"faqs": faqs, "categories": categories})


def terms(request):
    return simple_page(request, "core/legal.html", "Terms and Conditions")


def privacy(request):
    return simple_page(request, "core/legal.html", "Privacy Policy")


def ai_assistant(request):
    return render(request, "core/ai_assistant.html")


def search(request):
    query = request.GET.get("q", "").strip()
    courses = Course.objects.none()
    posts = BlogPost.objects.none()
    faqs = FAQ.objects.none()
    if query:
        courses = Course.objects.filter(status=Course.Status.PUBLISHED).filter(
            Q(title__icontains=query) | Q(subtitle__icontains=query) | Q(description__icontains=query)
        )[:8]
        posts = BlogPost.objects.filter(is_published=True).filter(
            Q(title__icontains=query) | Q(excerpt__icontains=query) | Q(content__icontains=query)
        )[:8]
        faqs = FAQ.objects.filter(is_active=True).filter(Q(question__icontains=query) | Q(answer__icontains=query))[:8]
    return render(request, "core/search.html", {"query": query, "courses": courses, "posts": posts, "faqs": faqs})
