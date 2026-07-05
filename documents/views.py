from django.db import transaction
from django.db.models import Count, Q
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from workspaces.permissions import get_user_workspace_ids
from .models import Document, DocumentVersion
from .serializers import DocumentSerializer, DocumentVersionSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    """
    POST /api/documents/ - Create a document and its first version
    PUT /api/documents/{id}/ - Update document and create a new version
    GET /api/documents/ - List documents with filtering by workspace, status, tag, or title
    GET /api/documents/{id}/versions/ - Get all versions of a document
    GET /api/documents/{id}/stats/ - Document statistics (version count, comment count, contributor count)
    POST /api/documents/{id}/tags/ - Add one or more tags to a document
    """
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["workspace", "status"]
    search_fields = ["title"]
    ordering_fields = ["created_at", "updated_at", "title"]

    def get_queryset(self):
        # Workspace scoping: only documents in workspaces the user belongs to.
        queryset = Document.objects.filter(workspace_id__in=get_user_workspace_ids(self.request.user))
        
        # Filter by tag if provided
        tag_name = self.request.query_params.get('tag')
        if tag_name:
            queryset = queryset.filter(tags__name=tag_name)
        
        return queryset

    @transaction.atomic
    def perform_create(self, serializer):
        content = serializer.validated_data.pop("content", "")
        document = serializer.save(created_by=self.request.user)
        version_number = document.versions.count() + 1
        DocumentVersion.objects.create(
            document=document, version_number=version_number, content=content, saved_by=self.request.user
        )

    @transaction.atomic
    def perform_update(self, serializer):
        """
        Editing a document never overwrites history. We lock the document
        row, work out the next version number inside the same transaction
        (so two simultaneous edits can't both compute the same number),
        write a fresh DocumentVersion, and only then update the Document's
        own metadata (title/status).
        """
        document = Document.objects.select_for_update().get(pk=self.get_object().pk)
        new_content = serializer.validated_data.pop("content", None)
        instance = serializer.save()

        if new_content is not None:
            version_number = document.versions.count() + 1
            DocumentVersion.objects.create(
                document=document,
                version_number=version_number,
                content=new_content,
                saved_by=self.request.user,
            )
        return instance

    @action(detail=True, methods=["get"])
    def versions(self, request, pk=None):
        """GET /api/documents/{id}/versions/ - Get all versions of a document"""
        document = self.get_object()
        qs = document.versions.all().order_by('version_number')
        return Response(DocumentVersionSerializer(qs, many=True).data)

    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        """GET /api/documents/{id}/stats/ - Document statistics"""
        from engagement.models import Comment
        
        document = self.get_object()
        version_count = document.versions.count()
        comment_count = document.comments.count()
        
        # Count unique contributors (users who saved versions)
        contributor_count = document.versions.values('saved_by').distinct().count()
        
        return Response({
            "version_count": version_count,
            "comment_count": comment_count,
            "contributor_count": contributor_count
        })

    @action(detail=True, methods=["post"])
    def tags(self, request, pk=None):
        """POST /api/documents/{id}/tags/ - Add one or more tags to a document"""
        from engagement.models import Tag
        
        document = self.get_object()
        tag_names = request.data.get("tags", [])
        
        if not isinstance(tag_names, list):
            tag_names = [tag_names]
        
        added_tags = []
        for tag_name in tag_names:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            tag.documents.add(document)
            added_tags.append(tag.name)
        
        return Response({"added_tags": added_tags}, status=status.HTTP_200_OK)
