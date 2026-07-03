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
    path("blog/<slug:slug>/", views.blog_detail, name="blog_detail"),
    path("blog/<slug:slug>/blocks/", views.manage_blog_blocks, name="manage_blog_blocks"),
    path("blog/<slug:slug>/blocks/reorder/", views.reorder_blog_blocks, name="reorder_blog_blocks"),
    path("blog/<slug:slug>/blocks/<int:block_id>/edit/", views.edit_blog_block, name="edit_blog_block"),
    path("blog/<slug:slug>/blocks/<int:block_id>/move/<str:direction>/", views.move_blog_block, name="move_blog_block"),
    path("blog/<slug:slug>/blocks/<int:block_id>/delete/", views.delete_blog_block, name="delete_blog_block"),
    path("help/", views.help_center, name="help_center"),
    path("ai-assistant/", views.ai_assistant, name="ai_assistant"),
    path("search/", views.search, name="search"),
    path("terms/", views.terms, name="terms"),
    path("privacy/", views.privacy, name="privacy"),
]
