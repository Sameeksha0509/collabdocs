from django.contrib import admin
from .models import Comment, Tag, AuditLog

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("document", "author", "created_at")

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "model_name", "object_id", "actor", "timestamp")
    list_filter = ("action", "model_name")
