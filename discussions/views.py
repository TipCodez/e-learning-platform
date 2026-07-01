from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from discussions.forms import DiscussionForm, DiscussionReplyForm
from discussions.models import Discussion


def discussion_list(request):
    discussions = Discussion.objects.select_related("course", "author").filter(is_hidden=False)
    return render(request, "discussions/list.html", {"discussions": discussions})


@login_required
def create_discussion(request):
    form = DiscussionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        discussion = form.save(commit=False)
        discussion.author = request.user
        discussion.save()
        messages.success(request, "Discussion posted.")
        return redirect("discussions:detail", discussion_id=discussion.id)
    return render(request, "discussions/form.html", {"form": form})


def discussion_detail(request, discussion_id):
    discussion = get_object_or_404(Discussion.objects.select_related("course", "author").prefetch_related("replies"), pk=discussion_id, is_hidden=False)
    form = DiscussionReplyForm()
    return render(request, "discussions/detail.html", {"discussion": discussion, "form": form})


@login_required
def reply(request, discussion_id):
    discussion = get_object_or_404(Discussion, pk=discussion_id)
    form = DiscussionReplyForm(request.POST)
    if form.is_valid():
        response = form.save(commit=False)
        response.discussion = discussion
        response.author = request.user
        response.is_instructor_reply = discussion.course.instructor == request.user
        response.save()
        messages.success(request, "Reply posted.")
    return redirect("discussions:detail", discussion_id=discussion.id)
