from django.contrib import admin
from .models import Document, ChatMessage, Project


class DocumentAdmin(admin.ModelAdmin):
    list_display = ('uploaded_at', 'file', 'user', 'type', 'content', 'summary',)


class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('is_bot_response', 'timestamp', 'user', 'message',)


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'scope', 'is_sitemap', 'is_url', 'is_youtube', 'is_multiple', 'uploaded_at', 'content',)


admin.site.register(Document, DocumentAdmin)
admin.site.register(ChatMessage, ChatMessageAdmin)
admin.site.register(Project, ProjectAdmin)
