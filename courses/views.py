from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from courses.forms import CourseForm, LessonForm, ModuleForm, ReviewForm
from courses.models import Category, Course, Lesson, LessonNote, Module, WishlistItem
from enrollments.models import CourseProgress, Enrollment, LessonProgress
from gamification.services import record_course_completion, record_lesson_completion


def course_list(request):
    courses = Course.objects.select_related("category", "instructor").filter(status=Course.Status.PUBLISHED)
    query = request.GET.get("q", "")
    category = request.GET.get("category", "")
    level = request.GET.get("level", "")
    price = request.GET.get("price", "")
    if query:
        courses = courses.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if category:
        courses = courses.filter(category__slug=category)
    if level:
        courses = courses.filter(level=level)
    if price == "free":
        courses = courses.filter(is_free=True)
    elif price == "paid":
        courses = courses.filter(is_free=False)
    paginator = Paginator(courses, 9)
    page = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "courses/course_list.html",
        {
            "page": page,
            "categories": Category.objects.filter(is_active=True),
            "levels": Course.Level.choices,
            "query": query,
            "selected_category": category,
            "selected_level": level,
            "selected_price": price,
        },
    )


def course_detail(request, slug):
    course = get_object_or_404(Course.objects.select_related("instructor", "category").prefetch_related("modules__lessons", "reviews"), slug=slug)
    if not course.is_published:
        can_preview = request.user.is_authenticated and (course.instructor == request.user or request.user.is_platform_admin)
        if not can_preview:
            messages.error(request, "This course is not published yet.")
            return redirect("courses:list")
    enrollment = None
    is_wishlisted = False
    if request.user.is_authenticated:
        enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
        is_wishlisted = WishlistItem.objects.filter(user=request.user, course=course).exists()
    review_form = ReviewForm()
    return render(
        request,
        "courses/course_detail.html",
        {
            "course": course,
            "enrollment": enrollment,
            "is_wishlisted": is_wishlisted,
            "review_form": review_form,
        },
    )


def categories(request):
    return render(request, "courses/categories.html", {"categories": Category.objects.prefetch_related("subcategories").filter(is_active=True)})


@login_required
def instructor_courses(request):
    if not (request.user.is_instructor or request.user.is_platform_admin):
        messages.error(request, "Instructor access required.")
        return redirect("dashboards:home")
    courses = Course.objects.filter(instructor=request.user).select_related("category").order_by("-created_at")
    return render(request, "courses/instructor_courses.html", {"courses": courses})


@login_required
def create_course(request):
    if not (request.user.is_instructor or request.user.is_platform_admin):
        messages.error(request, "Only instructors can create courses.")
        return redirect("dashboards:home")
    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            course.status = Course.Status.PENDING
            course.save()
            messages.success(request, "Course submitted for approval.")
            return redirect(course.get_absolute_url())
    else:
        form = CourseForm()
    return render(request, "courses/course_form.html", {"form": form, "title": "Create Course"})


@login_required
def edit_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if course.instructor != request.user and not request.user.is_platform_admin:
        messages.error(request, "You cannot edit another instructor's course.")
        return redirect("courses:detail", slug=slug)
    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Course updated.")
            return redirect(course.get_absolute_url())
    else:
        form = CourseForm(instance=course)
    return render(request, "courses/course_form.html", {"form": form, "title": "Edit Course"})


@login_required
def submit_for_approval(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if course.instructor != request.user and not request.user.is_platform_admin:
        messages.error(request, "You cannot submit this course.")
        return redirect("courses:detail", slug=slug)
    course.status = Course.Status.PENDING
    course.rejection_reason = ""
    course.save(update_fields=["status", "rejection_reason", "updated_at"])
    messages.success(request, "Course submitted for approval.")
    return redirect("courses:instructor_courses")


@login_required
def pending_courses(request):
    if not request.user.is_platform_admin:
        messages.error(request, "Admin access required.")
        return redirect("dashboards:home")
    courses = Course.objects.select_related("instructor", "category").filter(status=Course.Status.PENDING)
    return render(request, "courses/pending_courses.html", {"courses": courses})


@login_required
def approve_course(request, slug):
    if not request.user.is_platform_admin:
        messages.error(request, "Admin access required.")
        return redirect("dashboards:home")
    if request.method != "POST":
        messages.error(request, "Approval must be submitted from the moderation form.")
        return redirect("courses:pending")
    course = get_object_or_404(Course, slug=slug)
    course.status = Course.Status.PUBLISHED
    course.approved_at = timezone.now()
    course.rejection_reason = ""
    course.save(update_fields=["status", "approved_at", "rejection_reason", "updated_at"])
    messages.success(request, "Course approved and published.")
    return redirect("courses:pending")


@login_required
def reject_course(request, slug):
    if not request.user.is_platform_admin:
        messages.error(request, "Admin access required.")
        return redirect("dashboards:home")
    if request.method != "POST":
        messages.error(request, "Rejection must be submitted from the moderation form.")
        return redirect("courses:pending")
    course = get_object_or_404(Course, slug=slug)
    course.status = Course.Status.REJECTED
    course.rejection_reason = request.POST.get("reason", "Needs revision.")
    course.save(update_fields=["status", "rejection_reason", "updated_at"])
    messages.success(request, "Course rejected with feedback.")
    return redirect("courses:pending")


@login_required
def manage_modules(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if course.instructor != request.user and not request.user.is_platform_admin:
        messages.error(request, "You cannot manage this course.")
        return redirect("courses:detail", slug=slug)
    form = ModuleForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        module = form.save(commit=False)
        module.course = course
        module.save()
        messages.success(request, "Module added.")
        return redirect("courses:manage_modules", slug=slug)
    return render(request, "courses/manage_modules.html", {"course": course, "form": form})


@login_required
def manage_lessons(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if course.instructor != request.user and not request.user.is_platform_admin:
        messages.error(request, "You cannot manage this course.")
        return redirect("courses:detail", slug=slug)
    form = LessonForm(request.POST or None, request.FILES or None)
    form.fields["module"].queryset = course.modules.all()
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Lesson saved.")
        return redirect("courses:manage_lessons", slug=slug)
    return render(request, "courses/manage_lessons.html", {"course": course, "form": form})


@login_required
def submit_review(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            course.reviews.update_or_create(
                user=request.user,
                defaults={
                    "rating": form.cleaned_data["rating"],
                    "comment": form.cleaned_data["comment"],
                    "is_approved": True,
                },
            )
            messages.success(request, "Thanks for reviewing this course.")
    return redirect("courses:detail", slug=slug)


@login_required
def toggle_wishlist(request, slug):
    course = get_object_or_404(Course, slug=slug)
    item = WishlistItem.objects.filter(user=request.user, course=course).first()
    if item:
        item.delete()
        messages.success(request, "Course removed from your wishlist.")
    else:
        WishlistItem.objects.create(user=request.user, course=course)
        messages.success(request, "Course saved to your wishlist.")
    return redirect("courses:detail", slug=slug)


@login_required
def wishlist(request):
    items = WishlistItem.objects.select_related("course", "course__category").filter(user=request.user)
    return render(request, "courses/wishlist.html", {"items": items})


@login_required
def lesson_detail(request, slug, lesson_id):
    course = get_object_or_404(Course, slug=slug)
    lesson = get_object_or_404(Lesson.objects.prefetch_related("content_blocks"), pk=lesson_id, module__course=course)
    enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
    if not enrollment and not lesson.is_preview and course.instructor != request.user and not request.user.is_platform_admin:
        messages.error(request, "Enroll before viewing this lesson.")
        return redirect("courses:detail", slug=slug)
    note = LessonNote.objects.filter(user=request.user, lesson=lesson).first()
    return render(request, "courses/lesson_detail.html", {"course": course, "lesson": lesson, "enrollment": enrollment, "note": note})


@login_required
def save_lesson_note(request, slug, lesson_id):
    course = get_object_or_404(Course, slug=slug)
    lesson = get_object_or_404(Lesson, pk=lesson_id, module__course=course)
    enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
    if not enrollment and course.instructor != request.user and not request.user.is_platform_admin:
        messages.error(request, "Enroll before saving lesson notes.")
        return redirect("courses:detail", slug=slug)
    LessonNote.objects.update_or_create(
        user=request.user,
        lesson=lesson,
        defaults={
            "note": request.POST.get("note", ""),
            "is_bookmarked": bool(request.POST.get("is_bookmarked")),
        },
    )
    messages.success(request, "Lesson note saved.")
    return redirect("courses:lesson", slug=slug, lesson_id=lesson.id)


@login_required
@require_POST
def mark_lesson_complete(request, slug, lesson_id):
    course = get_object_or_404(Course, slug=slug)
    lesson = get_object_or_404(Lesson, pk=lesson_id, module__course=course)
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
    progress, _ = LessonProgress.objects.get_or_create(enrollment=enrollment, lesson=lesson)
    first_completion = not progress.completed
    was_completed = enrollment.status == Enrollment.Status.COMPLETED
    progress.mark_complete()
    course_progress, _ = CourseProgress.objects.get_or_create(enrollment=enrollment)
    course_progress.recalculate()
    if first_completion:
        record_lesson_completion(request.user, lesson)
    enrollment.refresh_from_db()
    if not was_completed and enrollment.status == Enrollment.Status.COMPLETED:
        record_course_completion(request, enrollment)
    messages.success(request, "Lesson marked complete.")
    return redirect("courses:lesson", slug=slug, lesson_id=lesson_id)
