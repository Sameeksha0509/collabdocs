from django.db.models import Count, Q
from rest_framework import viewsets, permissions, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from workspaces.permissions import get_user_workspace_ids
from documents.models import Document
from .models import Comment, Tag, AuditLog
from .serializers import CommentSerializer, TagSerializer, AuditLogSerializer


class CommentViewSet(viewsets.ModelViewSet):
    """
    POST /api/comments/ - Create a top-level comment or reply
    GET /api/comments/?document={id} - Get all comments for a document (threaded)
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["document"]

    def get_queryset(self):
        queryset = Comment.objects.filter(document__workspace_id__in=get_user_workspace_ids(self.request.user))
        
        # Filter by document if provided
        document_id = self.request.query_params.get('document')
        if document_id:
            queryset = queryset.filter(document_id=document_id)
        
        return queryset.select_related('author', 'parent')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TagViewSet(viewsets.ModelViewSet):
    """
    POST /api/tags/ - Create a new tag
    GET /api/tags/ - List all tags
    """
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ["name"]

    def get_queryset(self):
        return Tag.objects.all()


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/audit-logs/ - Filter audit logs by actor ID and date range
    """
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["actor"]
    queryset = AuditLog.objects.select_related("actor").all()

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by date range if provided
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)
        
        return queryset
