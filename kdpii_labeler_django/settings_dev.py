"""
Development settings for KDPII Labeler Django project.
Uses SQLite for easier development setup.
"""

from .settings import *

# Override database configuration for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Disable debug toolbar in development
DEBUG = True

# Allow all hosts for development
ALLOWED_HOSTS = ['*']

# Disable email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'