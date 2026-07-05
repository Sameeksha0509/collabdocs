from rest_framework import serializers
from .models import Comment, Tag, AuditLog


class CommentSerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source="author.email", read_only=True, allow_null=True)

    class Meta:
        model = Comment
        fields = ["id", "document", "author", "author_email", "parent", "content", "created_at"]
        read_only_fields = ["id", "author", "created_at"]


class TagSerializer(serializers.ModelSerializer):
    document_count = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ["id", "name", "document_count"]
        read_only_fields = ["id"]

    def get_document_count(self, obj):
        return obj.documents.count()


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True, allow_null=True)

    class Meta:
        model = AuditLog
        fields = ["id", "actor", "actor_email", "action", "model_name", "object_id", "timestamp"]
        read_only_fields = fields
