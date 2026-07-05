from rest_framework import permissions
from .models import WorkspaceMember


class IsWorkspaceMember(permissions.BasePermission):
    """
    Object-level permission: the requesting user must be a member of the
    workspace that owns the object being accessed. This is the core
    'workspace scoping' rule -- a user should never see or touch data
    belonging to a workspace they are not part of.
    """

    def has_object_permission(self, request, view, obj):
        workspace = getattr(obj, "workspace", None) or obj  # obj can be the Workspace itself
        return WorkspaceMember.objects.filter(workspace=workspace, user=request.user).exists()


class IsWorkspaceAdminOrEditor(permissions.BasePermission):
    """
    Write access (create/update/delete) is restricted to admins and editors.
    Viewers get read-only access, enforced here rather than trusted to the client.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        workspace = getattr(obj, "workspace", None) or obj
        membership = WorkspaceMember.objects.filter(workspace=workspace, user=request.user).first()
        return bool(membership and membership.role in (WorkspaceMember.Role.ADMIN, WorkspaceMember.Role.EDITOR))


def get_user_workspace_ids(user):
    """Helper used across apps (documents, engagement) to scope querysets to a user's workspaces."""
    return WorkspaceMember.objects.filter(user=user).values_list("workspace_id", flat=True)
