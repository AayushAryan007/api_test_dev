# account/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.utils import timezone
from .models import AuthToken
import logging

class CustomAuthMiddleware(MiddlewareMixin):
    """
    Custom authentication middleware for auth tokens.
    Validates token on every request, sets request.user if valid.
    """
    
    def process_request(self, request):
        """
        Called before view processing.
        Extracts token from Authorization header, validates it.
        """

        # check this while testing testing
        # Skip auth for certain paths (e.g., login, signup, static files)
        exempt_paths = ['/login', '/signup', '/admin', '/static', '/media']
        if any(request.path.startswith(path) for path in exempt_paths):
            return  # Skip middleware
        
        # Extract token: Header first (API), then cookie (web)
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        token_str = auth_header[7:] if auth_header.startswith('Bearer ') else request.COOKIES.get('auth_token')
        
        logging.info(f"Auth header: {auth_header}")
        logging.info(f"Token str: {token_str}")
        print(f"Token str: {token_str}")
        print(f"Auth header: {auth_header}")
        
        
        if not token_str:
            return self._unauthorized_response("Missing or invalid Authorization header")
        
        # Validate token
        try:
            token_obj = AuthToken.objects.get(token=token_str)
            logging.info(f"Token obj: {token_obj}, user: {token_obj.user}")
            logging.info(f"is_valid: {token_obj.is_valid()}, is_active: {token_obj.is_active}, status: {token_obj.status}")
            logging.info(f"expires_at: {token_obj.expires_at}, now: {timezone.now()}")
            
            if not token_obj.is_valid():
                if token_obj.expires_at <= timezone.now():
                    token_obj.status = 'expired'
                    token_obj.save()
                return self._unauthorized_response("Token expired or inactive")
            
            if not token_obj.user.is_active:
                return self._unauthorized_response("User is not active")
            
            # Token is valid: set request.user and token metadata
            request.user = token_obj.user
            request.auth_token = token_obj  # Optional: attach token object for views
            request.user_permissions = token_obj.permissions  # Optional: permissions
            
            logging.info(f"User set: {request.user}")
        except AuthToken.DoesNotExist:
            return self._unauthorized_response("Invalid token")
    
    def _unauthorized_response(self, message):
        """Return 401 Unauthorized response."""
        return JsonResponse({'error': message, 'status': 'unauthorized'}, status=401)
    
    def process_response(self, request, response):
        """
        Called after view processing.
        Optional: Add headers, log, etc.
        """
        # Example: Add custom header
        response['X-Auth-Status'] = 'validated' if hasattr(request, 'user') and request.user.is_authenticated else 'none'
        return response