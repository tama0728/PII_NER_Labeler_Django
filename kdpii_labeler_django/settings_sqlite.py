"""
Django settings for KDPII Labeler Django project with SQLite (for testing)
"""

from .settings import *

# Override database settings to use SQLite for testing
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db_test.sqlite3",
    }
}

# Disable CORS for testing
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

print("🔧 Using SQLite database for testing")
