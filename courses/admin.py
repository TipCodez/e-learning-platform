from django.contrib import admin

from courses.models import Category, Course, Lesson, LessonNote, LessonResource, Module, Review, SubCategory, WishlistItem


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "is_active", "created_at")
    search_fields = ("name",)


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "category")
    list_filter = ("category",)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    list_display = ("title", "instructor", "category", "level", "is_free", "status", "featured")
    list_filter = ("status", "level", "is_free", "featured", "category")
    search_fields = ("title", "description", "instructor__username")
    inlines = [ModuleInline]


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    list_filter = ("course",)
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    list_display = ("title", "module", "lesson_type", "order", "is_preview")
    list_filter = ("lesson_type", "is_preview")


admin.site.register(LessonResource)
admin.site.register(Review)
admin.site.register(WishlistItem)
admin.site.register(LessonNote)
