"""
Firebase client configuration for Alaa Academy
"""

import firebase_admin
from firebase_admin import credentials, storage, auth
from django.conf import settings
import logging
import json

logger = logging.getLogger(__name__)

class FirebaseClient:
    """Singleton Firebase client"""
    _instance = None
    _app = None
    _bucket = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._app is None:
            try:
                # Check if Firebase is already initialized
                if not firebase_admin._apps:
                    firebase_config = settings.FIREBASE_CONFIG
                    
                    if not firebase_config.get('project_id'):
                        logger.warning("Firebase configuration not found")
                        return
                    
                    # Create credentials from config
                    cred = credentials.Certificate(firebase_config)
                    
                    # Initialize Firebase app
                    self._app = firebase_admin.initialize_app(cred, {
                        'storageBucket': settings.FIREBASE_STORAGE_BUCKET
                    })
                    
                    logger.info("Firebase app initialized successfully")
                else:
                    self._app = firebase_admin.get_app()
                    logger.info("Using existing Firebase app")
                
                # Initialize storage bucket
                if settings.FIREBASE_STORAGE_BUCKET:
                    self._bucket = storage.bucket()
                    
            except Exception as e:
                logger.error(f"Failed to initialize Firebase: {e}")
                self._app = None
                self._bucket = None
    
    @property
    def app(self):
        """Get the Firebase app instance"""
        return self._app
    
    @property
    def bucket(self):
        """Get the Firebase storage bucket"""
        return self._bucket
    
    def is_connected(self) -> bool:
        """Check if Firebase is properly configured"""
        return self._app is not None
    
    def test_connection(self) -> bool:
        """Test the Firebase connection"""
        if not self.is_connected():
            return False
        
        try:
            # Try to list users to test connection
            auth.list_users(max_results=1)
            return True
        except Exception as e:
            logger.error(f"Firebase connection test failed: {e}")
            return False
    
    def upload_file(self, file_path: str, blob_name: str) -> str:
        """Upload a file to Firebase Storage"""
        if not self._bucket:
            raise Exception("Firebase Storage not initialized")
        
        try:
            blob = self._bucket.blob(blob_name)
            blob.upload_from_filename(file_path)
            blob.make_public()
            return blob.public_url
        except Exception as e:
            logger.error(f"Failed to upload file to Firebase Storage: {e}")
            raise
    
    def upload_file_from_memory(self, file_data: bytes, blob_name: str, content_type: str = None) -> str:
        """Upload file data from memory to Firebase Storage"""
        if not self._bucket:
            raise Exception("Firebase Storage not initialized")
        
        try:
            blob = self._bucket.blob(blob_name)
            if content_type:
                blob.content_type = content_type
            blob.upload_from_string(file_data)
            blob.make_public()
            return blob.public_url
        except Exception as e:
            logger.error(f"Failed to upload file data to Firebase Storage: {e}")
            raise
    
    def delete_file(self, blob_name: str) -> bool:
        """Delete a file from Firebase Storage"""
        if not self._bucket:
            return False
        
        try:
            blob = self._bucket.blob(blob_name)
            blob.delete()
            return True
        except Exception as e:
            logger.error(f"Failed to delete file from Firebase Storage: {e}")
            return False

# Global instance
firebase_client = FirebaseClient()

def get_firebase_client():
    """Get the global Firebase client instance"""
    return firebase_client

def test_firebase_connection() -> bool:
    """Test Firebase connection"""
    return firebase_client.test_connection()
