from django.db import transaction
from django.db.models import Count
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from .models import Workspace, WorkspaceMember
from .serializers import WorkspaceSerializer, WorkspaceMemberSerializer, AddMemberSerializer
from .permissions import IsWorkspaceMember, IsWorkspaceAdminOrEditor

User = get_user_model()


class WorkspaceViewSet(viewsets.ModelViewSet):
    """
    POST /api/workspaces/ - Create a workspace and automatically add owner as admin member
    GET /api/workspaces/{id}/ - Get workspace details including member count
    POST /api/workspaces/{id}/members/ - Add a member to a workspace
    GET /api/workspaces/{id}/members/ - List all members and their roles
    GET /api/workspaces/{id}/summary/ - Workspace summary (document count, member count, total comments)
    """
    serializer_class = WorkspaceSerializer
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceMember]

    def get_queryset(self):
        # Workspace scoping: a user only ever sees workspaces they are a member of.
        return Workspace.objects.filter(memberships__user=self.request.user).distinct()

    def get_serializer_context(self):
        return {"request": self.request}

    def get_permissions(self):
        if self.action == "create":
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    @transaction.atomic
    def perform_create(self, serializer):
        # Create workspace and automatically add owner as admin member in same transaction
        workspace = serializer.save(owner=self.request.user)
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=workspace.owner,
            role=WorkspaceMember.Role.ADMIN
        )

    def retrieve(self, request, *args, **kwargs):
        """GET /api/workspaces/{id}/ - Get workspace details including member count"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        data['member_count'] = instance.memberships.count()
        return Response(data)

    @action(detail=True, methods=["get", "post"])
    def members(self, request, pk=None):
        workspace = self.get_object()
        if request.method == "GET":
            memberships = workspace.memberships.select_related("user")
            return Response(WorkspaceMemberSerializer(memberships, many=True).data)

        # POST -- only admins/editors may add members.
        if not WorkspaceMember.objects.filter(
            workspace=workspace, user=request.user, role__in=["admin", "editor"]
        ).exists():
            return Response({"detail": "Only admins or editors can add members."}, status=status.HTTP_403_FORBIDDEN)

        serializer = AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(email__iexact=serializer.validated_data["email"])
        membership, created = WorkspaceMember.objects.get_or_create(
            workspace=workspace, user=user, defaults={"role": serializer.validated_data["role"]}
        )
        if not created:
            return Response({"detail": "User is already a member."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(WorkspaceMemberSerializer(membership).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        """GET /api/workspaces/{id}/summary/ - Workspace summary"""
        from documents.models import Document
        from engagement.models import Comment
        
        workspace = self.get_object()
        document_count = Document.objects.filter(workspace=workspace).count()
        member_count = workspace.memberships.count()
        comment_count = Comment.objects.filter(document__workspace=workspace).count()
        
        return Response({
            "document_count": document_count,
            "member_count": member_count,
            "comment_count": comment_count
        })
