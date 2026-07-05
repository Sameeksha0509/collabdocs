from rest_framework_simplejwt.authentication import JWTAuthentication
from .signals import set_current_user


class AuditMiddleware:
    """
    Stashes the current request's user in a thread-local so that model
    signals (which have no access to the request) know who to attribute
    the AuditLog entry to.

    Note: Django's AuthenticationMiddleware only populates request.user for
    session auth. DRF's JWTAuthentication normally runs later, inside the
    view, which is too late for middleware to see it -- so we resolve the
    JWT here ourselves, just for this purpose.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()

    def __call__(self, request):
        user = None
        try:
            result = self.jwt_auth.authenticate(request)
            if result is not None:
                user, _ = result
        except Exception:
            user = None
        set_current_user(user)
        response = self.get_response(request)
        set_current_user(None)
        return response
