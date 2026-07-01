from django.contrib import admin

from courses.models import Category, Course, Lesson, LessonContentBlock, LessonNote, LessonResource, Module, Review, SubCategory, WishlistItem


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 0


class LessonContentBlockInline(admin.StackedInline):
    model = LessonContentBlock
    extra = 1
    fields = (
        "order",
        "block_type",
        "title",
        "subtitle",
        "body",
        "code_language",
        "image",
        "image_alt",
        "table_data",
    )


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
    search_fields = ("title", "content", "module__course__title")
    inlines = [LessonContentBlockInline]


@admin.register(LessonContentBlock)
class LessonContentBlockAdmin(admin.ModelAdmin):
    list_display = ("lesson", "block_type", "order", "title", "updated_at")
    list_filter = ("block_type", "lesson__module__course")
    search_fields = ("lesson__title", "lesson__module__course__title", "title", "subtitle", "body", "table_data")


admin.site.register(LessonResource)
admin.site.register(Review)
admin.site.register(WishlistItem)
admin.site.register(LessonNote)