"""Root URL configuration for Acadeval."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from acadeval.views import health_check, public_media

urlpatterns = [
    path("health/", health_check, name="health_check"),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("dashboard/", include("dashboards.urls")),
    path("courses/", include("courses.urls")),
    path("learning/", include("enrollments.urls")),
    path("assessments/", include("assessments.urls")),
    path("certificates/", include("certificates.urls")),
    path("payments/", include("payments.urls")),
    path("achievements/", include("gamification.urls")),
    path("paths/", include("learning_paths.urls")),
    path("community/", include("discussions.urls")),
    path("notifications/", include("notifications.urls")),
    path("organizations/", include("organizations.urls")),
    path("career/", include("career.urls")),
    path("media/<path:path>", public_media, name="public_media"),
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

