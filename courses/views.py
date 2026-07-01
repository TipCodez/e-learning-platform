from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from courses.forms import CourseForm, LessonForm, ModuleForm, ReviewForm
from courses.models import Category, Course, Lesson, Module
from enrollments.models import CourseProgress, Enrollment, LessonProgress


def course_list(request):
    courses = Course.objects.select_related("category", "instructor").filter(status=Course.Status.PUBLISHED)
    query = request.GET.get("q", "")
    category = request.GET.get("category", "")
    level = request.GET.get("level", "")
    if query:
        courses = courses.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if category:
        courses = courses.filter(category__slug=category)
    if level:
        courses = courses.filter(level=level)
    paginator = Paginator(courses, 9)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "courses/course_list.html", {"page": page, "categories": Category.objects.filter(is_active=True), "query": query})


def course_detail(request, slug):
    course = get_object_or_404(Course.objects.select_related("instructor", "category").prefetch_related("modules__lessons", "reviews"), slug=slug)
    enrollment = None
    if request.user.is_authenticated:
        enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
    review_form = ReviewForm()
    return render(request, "courses/course_detail.html", {"course": course, "enrollment": enrollment, "review_form": review_form})


def categories(request):
    return render(request, "courses/categories.html", {"categories": Category.objects.prefetch_related("subcategories").filter(is_active=True)})


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
            review = form.save(commit=False)
            review.course = course
            review.user = request.user
            review.save()
            messages.success(request, "Thanks for reviewing this course.")
    return redirect("courses:detail", slug=slug)


@login_required
def lesson_detail(request, slug, lesson_id):
    course = get_object_or_404(Course, slug=slug)
    lesson = get_object_or_404(Lesson, pk=lesson_id, module__course=course)
    enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
    if not enrollment and not lesson.is_preview and course.instructor != request.user and not request.user.is_platform_admin:
        messages.error(request, "Enroll before viewing this lesson.")
        return redirect("courses:detail", slug=slug)
    return render(request, "courses/lesson_detail.html", {"course": course, "lesson": lesson, "enrollment": enrollment})


@login_required
def mark_lesson_complete(request, slug, lesson_id):
    course = get_object_or_404(Course, slug=slug)
    lesson = get_object_or_404(Lesson, pk=lesson_id, module__course=course)
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
    progress, _ = LessonProgress.objects.get_or_create(enrollment=enrollment, lesson=lesson)
    progress.mark_complete()
    course_progress, _ = CourseProgress.objects.get_or_create(enrollment=enrollment)
    course_progress.recalculate()
    messages.success(request, "Lesson marked complete.")
    return redirect("courses:lesson", slug=slug, lesson_id=lesson_id)
