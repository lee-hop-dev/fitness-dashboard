#!/usr/bin/env python3
"""
Google Drive Storage Manager
Handles uploading and downloading fitness data to/from Google Drive
"""

import os
import io
import json
from typing import Dict, List, Optional
from datetime import datetime

from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError


class GoogleDriveStorage:
    """Manager for Google Drive storage operations"""
    
    SCOPES = ['https://www.googleapis.com/auth/drive']
    
    def __init__(self, credentials_path: str, folder_structure: Dict[str, str]):
        """
        Initialize Google Drive storage
        
        Args:
            credentials_path: Path to credentials.json or service account key
            folder_structure: Dict with 'raw' and 'processed' folder paths
        """
        self.credentials_path = credentials_path
        self.folder_structure = folder_structure
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Drive API"""
        try:
            # Try service account first (for GitHub Actions)
            if os.path.exists(self.credentials_path):
                creds = service_account.Credentials.from_service_account_file(
                    self.credentials_path, scopes=self.SCOPES
                )
                self.service = build('drive', 'v3', credentials=creds)
                print("Authenticated with Google Drive (service account)")
            else:
                raise Exception(f"Credentials file not found: {self.credentials_path}")
                
        except Exception as e:
            print(f"Authentication failed: {e}")
            raise
    
    def _get_or_create_folder(self, folder_path: str, parent_id: Optional[str] = None) -> str:
        """
        Get folder ID or create if it doesn't exist
        
        Args:
            folder_path: Path like 'Github/Fitness/Raw'
            parent_id: Parent folder ID (None for root)
            
        Returns:
            Folder ID
        """
        # Split path into components
        parts = folder_path.strip('/').split('/')
        
        current_parent = parent_id
        
        for folder_name in parts:
            # Search for folder
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
            if current_parent:
                query += f" and '{current_parent}' in parents"
            query += " and trashed=false"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            items = results.get('files', [])
            
            if items:
                # Folder exists
                current_parent = items[0]['id']
            else:
                # Create folder
                file_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                if current_parent:
                    file_metadata['parents'] = [current_parent]
                
                folder = self.service.files().create(
                    body=file_metadata,
                    fields='id'
                ).execute()
                
                current_parent = folder.get('id')
                print(f"Created folder: {folder_name} (ID: {current_parent})")
        
        return current_parent
    
    def upload_json(self, data: Dict, filename: str, folder_type: str = 'raw') -> str:
        """
        Upload JSON data to Google Drive
        
        Args:
            data: Dictionary to upload as JSON
            filename: Filename (e.g., 'activities_2024-01-01.json')
            folder_type: 'raw' or 'processed'
            
        Returns:
            File ID of uploaded file
        """
        folder_path = self.folder_structure.get(folder_type)
        if not folder_path:
            raise ValueError(f"Unknown folder type: {folder_type}")
        
        # Get folder ID
        folder_id = self._get_or_create_folder(folder_path)
        
        # Check if file already exists
        query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
        results = self.service.files().list(q=query, fields='files(id)').execute()
        existing_files = results.get('files', [])
        
        # Create temporary file
        temp_path = f"/tmp/{filename}"
        with open(temp_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(temp_path, mimetype='application/json')
        
        try:
            if existing_files:
                # Update existing file
                file_id = existing_files[0]['id']
                file = self.service.files().update(
                    fileId=file_id,
                    media_body=media
                ).execute()
                print(f"Updated: {filename} in {folder_type}/")
            else:
                # Create new file
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                print(f"Uploaded: {filename} to {folder_type}/")
            
            # Clean up temp file
            os.remove(temp_path)
            
            return file.get('id')
            
        except HttpError as error:
            print(f"Upload failed: {error}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise
    
    def download_json(self, filename: str, folder_type: str = 'raw') -> Optional[Dict]:
        """
        Download JSON data from Google Drive
        
        Args:
            filename: Filename to download
            folder_type: 'raw' or 'processed'
            
        Returns:
            Dictionary from JSON file, or None if not found
        """
        folder_path = self.folder_structure.get(folder_type)
        if not folder_path:
            raise ValueError(f"Unknown folder type: {folder_type}")
        
        folder_id = self._get_or_create_folder(folder_path)
        
        # Search for file
        query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
        results = self.service.files().list(q=query, fields='files(id)').execute()
        files = results.get('files', [])
        
        if not files:
            print(f"File not found: {filename}")
            return None
        
        file_id = files[0]['id']
        
        # Download file
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        fh.seek(0)
        data = json.load(fh)
        print(f"Downloaded: {filename} from {folder_type}/")
        
        return data
    
    def list_files(self, folder_type: str = 'raw') -> List[Dict]:
        """
        List all files in a folder
        
        Args:
            folder_type: 'raw' or 'processed'
            
        Returns:
            List of file metadata dictionaries
        """
        folder_path = self.folder_structure.get(folder_type)
        folder_id = self._get_or_create_folder(folder_path)
        
        query = f"'{folder_id}' in parents and trashed=false"
        results = self.service.files().list(
            q=query,
            fields='files(id, name, createdTime, modifiedTime, size)'
        ).execute()
        
        return results.get('files', [])


def main():
    """Test the Google Drive storage"""
    import yaml
    
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
    
    if not os.path.exists(config_path):
        print("Config file not found")
        return
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize storage
    storage = GoogleDriveStorage(
        credentials_path=config['google_drive']['credentials_file'],
        folder_structure={
            'raw': config['google_drive']['raw_folder'],
            'processed': config['google_drive']['processed_folder']
        }
    )
    
    # Test upload
    test_data = {
        'test': True,
        'timestamp': datetime.now().isoformat(),
        'message': 'Google Drive integration test'
    }
    
    storage.upload_json(test_data, 'test.json', 'raw')
    
    # Test download
    downloaded = storage.download_json('test.json', 'raw')
    print(f"\nDownloaded test data: {downloaded}")
    
    # List files
    files = storage.list_files('raw')
    print(f"\nFiles in raw folder: {len(files)}")
    for file in files:
        print(f"  - {file['name']}")


if __name__ == "__main__":
    main()
