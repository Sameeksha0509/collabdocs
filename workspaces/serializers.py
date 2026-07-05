from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Workspace, WorkspaceMember

User = get_user_model()


class WorkspaceMemberSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = WorkspaceMember
        fields = ["id", "workspace", "user", "user_email", "role", "joined_at"]
        read_only_fields = ["id", "joined_at", "workspace"]


class AddMemberSerializer(serializers.Serializer):
    """Add a member by email rather than raw user id -- friendlier for API consumers."""
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=WorkspaceMember.Role.choices, default=WorkspaceMember.Role.VIEWER)

    def validate_email(self, value):
        if not User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("No user with this email exists.")
        return value


class WorkspaceSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = ["id", "name", "owner", "member_count", "created_at"]
        read_only_fields = ["id", "owner", "created_at"]

    def get_member_count(self, obj):
        return obj.memberships.count()
