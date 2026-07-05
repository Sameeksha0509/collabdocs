from rest_framework.routers import DefaultRouter
from .views import CommentViewSet, TagViewSet, AuditLogViewSet

router = DefaultRouter()
router.register("comments", CommentViewSet, basename="comment")
router.register("tags", TagViewSet, basename="tag")
router.register("audit-logs", AuditLogViewSet, basename="auditlog")

urlpatterns = router.urls
