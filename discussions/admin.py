from django.contrib import admin

from discussions.models import Announcement, Discussion, DiscussionReply

admin.site.register(Discussion)
admin.site.register(DiscussionReply)
admin.site.register(Announcement)
