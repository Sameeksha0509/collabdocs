import uuid
from django.db import models
from django.conf import settings
from workspaces.models import Workspace


class Document(models.Model):
    """
    A document lives in exactly one workspace. Content itself is NOT stored
    here -- it lives in DocumentVersion, so 'the document' is really just the
    stable identity + metadata, and 'the content' is whichever version is current.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    content = models.TextField(default="")
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="documents")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="documents_created"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

    @property
    def current_version(self):
        return self.versions.order_by("-version_number").first()


class DocumentVersion(models.Model):
    """
    Every save creates a NEW version rather than mutating the previous one --
    this is what the brief means by 'never overwrite an existing
    DocumentVersion; the same transaction.atomic() block'. version_number is
    assigned inside a transaction so two concurrent saves can never collide
    on the same number.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="versions")
    version_number = models.PositiveIntegerField()
    content = models.TextField()
    saved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="document_versions"
    )
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version_number"]
        constraints = [
            models.UniqueConstraint(fields=["document", "version_number"], name="unique_document_version_number")
        ]

    def __str__(self):
        return f"{self.document.title} v{self.version_number}"
