"""
Management command to test database connections
"""

from django.core.management.base import BaseCommand
from django.db import connection
from alaa_academy.supabase_client import test_supabase_connection
from alaa_academy.firebase_client import test_firebase_connection


class Command(BaseCommand):
    help = 'Test database and external service connections'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing connections...'))
        
        # Test Django database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                self.stdout.write(
                    self.style.SUCCESS('✓ Django database connection: OK')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Django database connection: FAILED - {e}')
            )
        
        # Test Supabase connection
        try:
            if test_supabase_connection():
                self.stdout.write(
                    self.style.SUCCESS('✓ Supabase connection: OK')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('⚠ Supabase connection: Not configured or failed')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Supabase connection: FAILED - {e}')
            )
        
        # Test Firebase connection
        try:
            if test_firebase_connection():
                self.stdout.write(
                    self.style.SUCCESS('✓ Firebase connection: OK')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('⚠ Firebase connection: Not configured or failed')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Firebase connection: FAILED - {e}')
            )
        
        self.stdout.write(self.style.SUCCESS('\nConnection testing completed!'))
