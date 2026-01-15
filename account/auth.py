from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import AuthToken


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            raw_token = request.COOKIES.get('access')
        else:
            raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token


class AuthTokenAuthentication(BaseAuthentication):
    """DRF authentication using our AuthToken model and Bearer header."""

    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header:
            return None

        if not auth_header.startswith(f"{self.keyword} "):
            return None

        token_str = auth_header[len(self.keyword) + 1 :].strip()
        if not token_str:
            return None

        try:
            token_obj = AuthToken.objects.get(token=token_str)
        except AuthToken.DoesNotExist:
            raise AuthenticationFailed("Invalid token")

        if not token_obj.is_valid() or not token_obj.user.is_active:
            raise AuthenticationFailed("Token expired or inactive")

        # Attach token for later use if needed
        request.auth_token = token_obj
        return token_obj.user, token_obj

    