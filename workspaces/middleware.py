import logging
import time

logger = logging.getLogger("collabdocs.request")


class RequestLoggingMiddleware:
    """
    Custom middleware (non-functional requirement): logs method, path,
    response status, authenticated user and duration for every API request.
    This gives the team a single place to see who touched what, and is a
    lightweight companion to the AuditLog model (which only tracks writes
    on specific models, not every request).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = (time.monotonic() - start) * 1000
        user = getattr(request, "user", None)
        user_repr = user.email if getattr(user, "is_authenticated", False) else "anonymous"
        logger.info(
            "%s %s -> %s (%.1fms) user=%s",
            request.method, request.path, response.status_code, duration_ms, user_repr,
        )
        return response
