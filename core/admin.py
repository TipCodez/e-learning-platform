from django.contrib import admin

from core.models import AIAssistantSession, BlogContentBlock, BlogPost, FAQ, SupportTicket

admin.site.register(AIAssistantSession)


class BlogContentBlockInline(admin.StackedInline):
    model = BlogContentBlock
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


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    list_display = ("title", "author", "is_published", "published_at", "updated_at")
    list_filter = ("is_published", "published_at")
    search_fields = ("title", "excerpt", "content")
    inlines = [BlogContentBlockInline]


@admin.register(BlogContentBlock)
class BlogContentBlockAdmin(admin.ModelAdmin):
    list_display = ("post", "block_type", "order", "title", "updated_at")
    list_filter = ("block_type", "post")
    search_fields = ("post__title", "title", "subtitle", "body", "table_data")


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "category", "order", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("question", "answer")


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("subject", "email", "status", "priority", "created_at")
    list_filter = ("status", "priority", "created_at")
    search_fields = ("subject", "message", "email", "name")