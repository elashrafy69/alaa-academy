web: python manage.py migrate && python manage.py collectstatic --noinput && python setup_production.py && gunicorn alaa_academy.wsgi --bind 0.0.0.0:$PORT
