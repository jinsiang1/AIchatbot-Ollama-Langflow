import requests
from django.conf import settings
from astrapy.db import AstraDB
from datetime import datetime

class AstraService:
    def __init__(self):
        self.db = AstraDB(
            token=settings.ASTRA_DB_SETTINGS['TOKEN'],
            api_endpoint=settings.ASTRA_DB_SETTINGS['API_ENDPOINT']
        )
        self.collection = self.db.collection('training_data')
        if not self.collection:
            self.collection = self.db.create_collection('training_data')

    def upload_training_file(self, file_content, metadata):
        """Upload training file to Astra DB"""
        try:
            document = {
                'content': file_content,
                'metadata': metadata,
                'uploaded_at': datetime.now().isoformat(),
                'status': 'pending',
                'type': 'training'
            }
            result = self.collection.insert_one(document)
            return result

        except Exception as e:
            print(f"Astra DB upload error: {e}")
            raise

    def get_training_files(self):
        """Get list of training files"""
        try:
            query = {"type": "training"}
            return self.collection.find(query)
        except Exception as e:
            print(f"Astra DB query error: {e}")
            return []

    def delete_training_file(self, file_id):
        """Delete a training file"""
        try:
            return self.collection.delete_one({"_id": file_id})
        except Exception as e:
            print(f"Astra DB deletion error: {e}")
            raise

    def get_file_by_id(self, file_id):
        """Get a specific training file by ID"""
        try:
            return self.collection.find_one({"_id": file_id})
        except Exception as e:
            print(f"Astra DB query error: {e}")
            return None

    def update_file_status(self, file_id, status):
        """Update the status of a training file"""
        try:
            return self.collection.update_one(
                {"_id": file_id},
                {"$set": {"status": status}}
            )
        except Exception as e:
            print(f"Astra DB update error: {e}")
            raise

    def test_connection(self):
        """Test the Astra DB connection"""
        try:
            collections = self.db.get_collections()
            print("Connected to Astra DB successfully")
            print("Available collections:", collections)
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False