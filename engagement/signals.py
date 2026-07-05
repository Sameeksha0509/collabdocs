from django.db.models.signals import post_save
from django.dispatch import receiver

from documents.models import Document
from .models import AuditLog

# We track the "current actor" per-request via a thread-local set by
# AuditMiddleware, because signals don't otherwise know who is logged in.
import threading

_local = threading.local()


def set_current_user(user):
    _local.user = user


def get_current_user():
    return getattr(_local, "user", None)


@receiver(post_save, sender=Document)
def log_document_save(sender, instance, **kwargs):
    """
    Automatically creates an AuditLog entry when a Document is created or updated.
    Uses instance._state.adding to determine if it's a create or update action.
    """
    action = "created" if instance._state.adding else "updated"
    AuditLog.objects.create(
        actor=get_current_user(),
        action=action,
        model_name="Document",
        object_id=str(instance.pk),
    )
