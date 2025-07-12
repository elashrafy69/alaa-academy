"""
Firebase Functions للتعامل مع Django
"""

import os
import sys
from pathlib import Path

# إضافة مسار المشروع
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# تعيين متغير البيئة لإعدادات Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alaa_academy.settings')

import django
from django.core.wsgi import get_wsgi_application
from firebase_functions import https_fn

# تهيئة Django
django.setup()

# الحصول على تطبيق WSGI
django_app = get_wsgi_application()


@https_fn.on_request(
    cors=https_fn.CorsOptions(
        cors_origins=["https://marketwise-academy-qhizq.web.app"],
        cors_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        cors_allow_headers=["Content-Type", "Authorization", "X-CSRFToken"],
        cors_max_age=3600,
    )
)
def app(req: https_fn.Request) -> https_fn.Response:
    """
    دالة Firebase الرئيسية للتعامل مع طلبات Django
    """
    
    # تحويل طلب Firebase إلى طلب WSGI
    environ = {
        'REQUEST_METHOD': req.method,
        'SCRIPT_NAME': '',
        'PATH_INFO': req.path,
        'QUERY_STRING': req.query_string,
        'CONTENT_TYPE': req.headers.get('content-type', ''),
        'CONTENT_LENGTH': str(len(req.data)) if req.data else '0',
        'SERVER_NAME': 'marketwise-academy-qhizq.web.app',
        'SERVER_PORT': '443',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https',
        'wsgi.input': req.stream,
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    
    # إضافة headers
    for key, value in req.headers.items():
        key = key.upper().replace('-', '_')
        if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            environ[f'HTTP_{key}'] = value
    
    # تشغيل Django
    response_data = []
    
    def start_response(status, headers, exc_info=None):
        response_data.extend([status, headers])
    
    result = django_app(environ, start_response)
    
    # تحويل استجابة Django إلى استجابة Firebase
    status_code = int(response_data[0].split(' ')[0])
    headers = dict(response_data[1])
    
    # جمع محتوى الاستجابة
    content = b''.join(result)
    
    return https_fn.Response(
        response=content,
        status=status_code,
        headers=headers
    )
