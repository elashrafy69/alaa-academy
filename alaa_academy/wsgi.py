"""
WSGI config for alaa_academy project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys
from django.core.wsgi import get_wsgi_application

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alaa_academy.settings')

try:
    application = get_wsgi_application()
except Exception as e:
    print(f"Error loading Django application: {e}")
    raise

# Vercel handler
app = application
