from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from courses.models import Course, Lesson
from discussions.forms import DiscussionForm, DiscussionReplyForm, DiscussionReportForm
from discussions.models import Discussion, DiscussionReport, DiscussionVote
from enrollments.models import Enrollment
from notifications.models import Notification


def _can_participate(user, course):
    if not user.is_authenticated:
        return False
    return (
        course.instructor == user
        or user.is_platform_admin
        or Enrollment.objects.filter(student=user, course=course).exists()
    )


def _discussion_url(discussion):
    return reverse("discussions:detail", kwargs={"discussion_id": discussion.id})


def discussion_list(request):
    discussions = Discussion.objects.select_related("course", "lesson", "author").filter(is_hidden=False)
    query = request.GET.get("q", "").strip()
    course_slug = request.GET.get("course", "").strip()
    if query:
        discussions = discussions.filter(Q(title__icontains=query) | Q(body__icontains=query))
    if course_slug:
        discussions = discussions.filter(course__slug=course_slug)
    discussions = discussions.annotate(reply_count=Count("replies"), vote_count=Count("votes")).order_by("-created_at")
    return render(
        request,
        "discussions/list.html",
        {
            "discussions": discussions,
            "courses": Course.objects.filter(status=Course.Status.PUBLISHED).order_by("title"),
            "query": query,
            "selected_course": course_slug,
        },
    )


@login_required
def create_discussion(request, slug=None):
    if not slug:
        messages.info(request, "Choose a course before starting a discussion.")
        return redirect("courses:list")
    course = get_object_or_404(Course, slug=slug, status=Course.Status.PUBLISHED)
    if not _can_participate(request.user, course):
        messages.error(request, "Enroll before starting a discussion for this course.")
        return redirect("courses:detail", slug=course.slug)

    form = DiscussionForm(request.POST or None)
    form.fields["lesson"].queryset = Lesson.objects.filter(module__course=course)
    form.fields["lesson"].required = False
    if request.method == "POST" and form.is_valid():
        discussion = form.save(commit=False)
        discussion.course = course
        discussion.author = request.user
        discussion.save()
        if course.instructor != request.user:
            Notification.objects.get_or_create(
                user=course.instructor,
                title="New course discussion",
                notification_type=Notification.Type.SYSTEM,
                link=_discussion_url(discussion),
                defaults={"message": f"{request.user.email} asked a question in {course.title}."},
            )
        messages.success(request, "Discussion posted.")
        return redirect("discussions:detail", discussion_id=discussion.id)
    return render(request, "discussions/form.html", {"form": form, "course": course})


def discussion_detail(request, discussion_id):
    discussion = get_object_or_404(
        Discussion.objects.select_related("course", "course__instructor", "lesson", "author").prefetch_related("replies__author"),
        pk=discussion_id,
        is_hidden=False,
    )
    can_participate = _can_participate(request.user, discussion.course)
    has_voted = request.user.is_authenticated and DiscussionVote.objects.filter(discussion=discussion, user=request.user).exists()
    form = DiscussionReplyForm()
    report_form = DiscussionReportForm()
    return render(
        request,
        "discussions/detail.html",
        {
            "discussion": discussion,
            "form": form,
            "report_form": report_form,
            "can_participate": can_participate,
            "has_voted": has_voted,
        },
    )


@login_required
@require_POST
def reply(request, discussion_id):
    discussion = get_object_or_404(Discussion.objects.select_related("course", "author", "course__instructor"), pk=discussion_id, is_hidden=False)
    if not _can_participate(request.user, discussion.course):
        messages.error(request, "Enroll before replying to this discussion.")
        return redirect("courses:detail", slug=discussion.course.slug)
    form = DiscussionReplyForm(request.POST)
    if form.is_valid():
        response = form.save(commit=False)
        response.discussion = discussion
        response.author = request.user
        response.is_instructor_reply = discussion.course.instructor == request.user
        response.save()
        recipients = {discussion.author_id, discussion.course.instructor_id} - {request.user.id}
        for user_id in recipients:
            Notification.objects.get_or_create(
                user_id=user_id,
                title="New discussion reply",
                notification_type=Notification.Type.SYSTEM,
                link=_discussion_url(discussion),
                defaults={"message": f"{request.user.email} replied to {discussion.title}."},
            )
        messages.success(request, "Reply posted.")
    return redirect("discussions:detail", discussion_id=discussion.id)


@login_required
@require_POST
def vote(request, discussion_id):
    discussion = get_object_or_404(Discussion, pk=discussion_id, is_hidden=False)
    vote_obj, created = DiscussionVote.objects.get_or_create(discussion=discussion, user=request.user)
    if created:
        messages.success(request, "Discussion upvoted.")
    else:
        vote_obj.delete()
        messages.info(request, "Upvote removed.")
    discussion.upvotes = DiscussionVote.objects.filter(discussion=discussion).count()
    discussion.save(update_fields=["upvotes"])
    return redirect("discussions:detail", discussion_id=discussion.id)


@login_required
@require_POST
def report(request, discussion_id):
    discussion = get_object_or_404(Discussion.objects.select_related("course", "course__instructor"), pk=discussion_id, is_hidden=False)
    form = DiscussionReportForm(request.POST)
    if form.is_valid():
        DiscussionReport.objects.update_or_create(
            discussion=discussion,
            reported_by=request.user,
            defaults={"reason": form.cleaned_data["reason"], "reviewed": False},
        )
        discussion.is_reported = True
        discussion.save(update_fields=["is_reported"])
        Notification.objects.get_or_create(
            user=discussion.course.instructor,
            title="Discussion reported",
            notification_type=Notification.Type.SYSTEM,
            link=_discussion_url(discussion),
            defaults={"message": f"A discussion in {discussion.course.title} was reported for review."},
        )
        messages.success(request, "Report submitted for review.")
    return redirect("discussions:detail", discussion_id=discussion.id)