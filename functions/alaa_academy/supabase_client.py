"""
Supabase client configuration for Alaa Academy
"""

from supabase import create_client, Client
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Singleton Supabase client"""
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            try:
                url = settings.SUPABASE_URL
                key = settings.SUPABASE_KEY
                
                if not url or not key:
                    logger.warning("Supabase URL or Key not configured")
                    self._client = None
                else:
                    self._client = create_client(url, key)
                    logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                self._client = None
    
    @property
    def client(self) -> Client:
        """Get the Supabase client instance"""
        return self._client
    
    def is_connected(self) -> bool:
        """Check if Supabase client is properly configured"""
        return self._client is not None
    
    def test_connection(self) -> bool:
        """Test the Supabase connection"""
        if not self.is_connected():
            return False
        
        try:
            # Try to fetch from a system table to test connection
            response = self._client.table('information_schema.tables').select('table_name').limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase connection test failed: {e}")
            return False

# Global instance
supabase_client = SupabaseClient()

def get_supabase_client() -> Client:
    """Get the global Supabase client instance"""
    return supabase_client.client

def test_supabase_connection() -> bool:
    """Test Supabase connection"""
    return supabase_client.test_connection()
