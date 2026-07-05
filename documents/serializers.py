from rest_framework import serializers
from .models import Document, DocumentVersion


class DocumentVersionSerializer(serializers.ModelSerializer):
    saved_by_email = serializers.EmailField(source="saved_by.email", read_only=True)

    class Meta:
        model = DocumentVersion
        fields = ["id", "document", "version_number", "content", "saved_by", "saved_by_email", "saved_at"]
        read_only_fields = ["id", "document", "version_number", "saved_by", "saved_at"]


class DocumentSerializer(serializers.ModelSerializer):
    latest_version_number = serializers.SerializerMethodField()
    content = serializers.CharField(write_only=True, required=False, help_text="Initial content for version 1")

    class Meta:
        model = Document
        fields = [
            "id", "workspace", "title", "status", "created_by",
            "latest_version_number", "content", "updated_at",
        ]
        read_only_fields = ["id", "created_by", "updated_at", "workspace"]

    def get_latest_version_number(self, obj):
        latest = obj.current_version
        return latest.version_number if latest else 0
