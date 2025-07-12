"""
WSGI config for production deployment
"""

import os
import sys
from django.core.wsgi import get_wsgi_application

# Add the project directory to the Python path
path = '/home/yourusername/alaa-academy'  # Update this path
if path not in sys.path:
    sys.path.insert(0, path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alaa_academy.settings')

application = get_wsgi_application()
