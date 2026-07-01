from django.shortcuts import get_object_or_404, render

from learning_paths.models import LearningPath


def path_list(request):
    paths = LearningPath.objects.prefetch_related("path_courses__course").all()
    return render(request, "learning_paths/list.html", {"paths": paths})


def path_detail(request, slug):
    learning_path = get_object_or_404(LearningPath.objects.prefetch_related("path_courses__course"), slug=slug)
    return render(request, "learning_paths/detail.html", {"learning_path": learning_path})
