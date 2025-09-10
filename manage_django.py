#!/usr/bin/env python3
"""
Django management script for KDPII Labeler
"""
import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kdpii_labeler_django.settings")


def main():
    """Run administrative tasks."""
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # For development, use SQLite if PostgreSQL is not available
    if len(sys.argv) > 1 and sys.argv[1] in ["migrate", "runserver", "test"]:
        # Override database settings to use SQLite for testing
        from django.conf import settings

        if not settings.configured:
            django.setup()

        # Check if PostgreSQL is available
        try:
            import psycopg2

            conn = psycopg2.connect(
                host="localhost",
                port="5432",
                user="postgres",
                password="password",
                database="postgres",
            )
            conn.close()
            print("✅ PostgreSQL connection successful - using PostgreSQL")
        except Exception as e:
            print(f"⚠️  PostgreSQL not available ({e}) - using SQLite for testing")
            # Temporarily override database settings
            settings.DATABASES = {
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": os.path.join(os.path.dirname(__file__), "db_test.sqlite3"),
                }
            }

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
