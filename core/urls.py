from django.urls import path

from core import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("courses/", views.courses, name="courses"),
    path("categories/", views.categories, name="categories"),
    path("learning-paths/", views.learning_paths, name="learning_paths"),
    path("certificates/verify/", views.certificate_verify, name="certificate_verify"),
    path("pricing/", views.pricing, name="pricing"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("become-an-instructor/", views.become_instructor, name="become_instructor"),
    path("organization-training/", views.organization_training, name="organization_training"),
    path("blog/", views.blog, name="blog"),
    path("help/", views.help_center, name="help_center"),
    path("terms/", views.terms, name="terms"),
    path("privacy/", views.privacy, name="privacy"),
]
