from django.urls import path

from courses import views

app_name = "courses"

urlpatterns = [
    path("", views.course_list, name="list"),
    path("categories/", views.categories, name="categories"),
    path("create/", views.create_course, name="create"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("instructor/my-courses/", views.instructor_courses, name="instructor_courses"),
    path("admin/pending/", views.pending_courses, name="pending"),
    path("<slug:slug>/", views.course_detail, name="detail"),
    path("<slug:slug>/edit/", views.edit_course, name="edit"),
    path("<slug:slug>/submit/", views.submit_for_approval, name="submit"),
    path("<slug:slug>/approve/", views.approve_course, name="approve"),
    path("<slug:slug>/reject/", views.reject_course, name="reject"),
    path("<slug:slug>/modules/", views.manage_modules, name="manage_modules"),
    path("<slug:slug>/lessons/", views.manage_lessons, name="manage_lessons"),
    path("<slug:slug>/lessons/<int:lesson_id>/blocks/", views.manage_lesson_blocks, name="manage_lesson_blocks"),
    path("<slug:slug>/lessons/<int:lesson_id>/blocks/<int:block_id>/edit/", views.edit_lesson_block, name="edit_lesson_block"),
    path("<slug:slug>/lessons/<int:lesson_id>/blocks/<int:block_id>/move/<str:direction>/", views.move_lesson_block, name="move_lesson_block"),
    path("<slug:slug>/lessons/<int:lesson_id>/blocks/<int:block_id>/delete/", views.delete_lesson_block, name="delete_lesson_block"),
    path("<slug:slug>/reviews/", views.submit_review, name="review"),
    path("<slug:slug>/wishlist/", views.toggle_wishlist, name="toggle_wishlist"),
    path("<slug:slug>/lessons/<int:lesson_id>/", views.lesson_detail, name="lesson"),
    path("<slug:slug>/lessons/<int:lesson_id>/notes/", views.save_lesson_note, name="save_lesson_note"),
    path("<slug:slug>/lessons/<int:lesson_id>/complete/", views.mark_lesson_complete, name="complete_lesson"),
]
