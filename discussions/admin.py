from django.contrib import admin

from discussions.models import Announcement, Discussion, DiscussionReply, DiscussionReport, DiscussionVote

admin.site.register(Discussion)
admin.site.register(DiscussionReply)
admin.site.register(DiscussionVote)
admin.site.register(DiscussionReport)
admin.site.register(Announcement)