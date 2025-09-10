import re
from django.middleware.csrf import CsrfViewMiddleware
from django.conf import settings


class CustomCsrfMiddleware(CsrfViewMiddleware):
    """Custom CSRF middleware that exempts API endpoints"""
    
    def process_view(self, request, callback, callback_args, callback_kwargs):
        # Check if the URL matches any exempt pattern
        if hasattr(settings, 'CSRF_EXEMPT_URLS'):
            for pattern in settings.CSRF_EXEMPT_URLS:
                if re.match(pattern, request.path):
                    return None  # Skip CSRF check
        
        # Apply normal CSRF processing
        return super().process_view(request, callback, callback_args, callback_kwargs)