"""
Google Drive Sync Script
Uploads local JSON files to Google Drive using a Service Account.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# ------------------ Logging ------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ------------------ Constants ------------------
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


# ------------------ Google Drive Sync Class ------------------
class GoogleDriveSync:
    def __init__(self):
        """Authenticate using Service Account from environment variables"""
        service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        self.folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

        if not service_account_json or not self.folder_id:
            raise ValueError(
                "GOOGLE_SERVICE_ACCOUNT_JSON and GOOGLE_DRIVE_FOLDER_ID must be set"
            )

        credentials = service_account.Credentials.from_service_account_info(
            json.loads(service_account_json), scopes=SCOPES
        )
        self.service = build("drive", "v3", credentials=credentials)
        self.subfolder_ids = self._get_or_create_subfolders()

    # ------------------ Subfolder Handling ------------------
    def _get_or_create_subfolders(self) -> dict:
        subfolder_names = ["raw", "processed", "cache"]
        ids = {}
        for name in subfolder_names:
            ids[name] = self._find_or_create_folder(name, self.folder_id)
            logger.info(f"Subfolder '{name}' ID: {ids[name]}")
        return ids

    def _find_or_create_folder(self, name: str, parent_id: str) -> str:
        """Find a folder or create it if missing"""
        query = (
            f"name='{name}' and '{parent_id}' in parents "
            "and mimeType='application/vnd.google-apps.folder' and trashed=false"
        )
        try:
            results = self.service.files().list(
                q=query, spaces="drive", fields="files(id, name)"
            ).execute()
            files = results.get("files", [])
            if files:
                return files[0]["id"]

            # Create folder if not found
            folder = self.service.files().create(
                body={"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]},
                fields="id",
            ).execute()
            return folder["id"]
        except HttpError as e:
            logger.error(f"Error accessing folder '{name}': {e}")
            raise

    # ------------------ File Upload ------------------
    def upload_file(self, filepath: Path, subfolder: str = "processed") -> Optional[str]:
        if not filepath.exists():
            logger.warning(f"File not found: {filepath}")
            return None

        parent_id = self.subfolder_ids.get(subfolder, self.folder_id)

        # Check if file exists
        existing_id = self._find_file(filepath.name, parent_id)
        media = MediaFileUpload(str(filepath), mimetype="application/json", resumable=True)
        file_metadata = {"name": filepath.name, "parents": [parent_id]}

        try:
            if existing_id:
                logger.info(f"Updating file: {filepath.name}")
                uploaded_file = self.service.files().update(
                    fileId=existing_id, media_body=media, fields="id"
                ).execute()
            else:
                logger.info(f"Uploading new file: {filepath.name}")
                uploaded_file = self.service.files().create(
                    body=file_metadata, media_body=media, fields="id"
                ).execute()
            return uploaded_file["id"]
        except HttpError as e:
            logger.error(f"Failed to upload {filepath.name}: {e}")
            return None

    def _find_file(self, filename: str, parent_id: str) -> Optional[str]:
        """Return file ID if it exists"""
        query = f"name='{filename}' and '{parent_id}' in parents and trashed=false"
        try:
            results = self.service.files().list(q=query, spaces="drive", fields="files(id)").execute()
            files = results.get("files", [])
            return files[0]["id"] if files else None
        except HttpError:
            return None

    # ------------------ Directory Sync ------------------
    def sync_directory(self, local_dir: Path, subfolder: str = "processed") -> int:
        if not local_dir.exists():
            logger.warning(f"Directory not found: {local_dir}")
            return 0
        uploaded_count = 0
        for f in local_dir.glob("*.json"):
            if self.upload_file(f, subfolder):
                uploaded_count += 1
        logger.info(f"Uploaded {uploaded_count} files from {local_dir}")
        return uploaded_count


# ------------------ Main ------------------
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Sync local JSON files to Google Drive")
    parser.add_argument("--upload-raw", action="store_true", help="Upload raw files")
    parser.add_argument("--upload-processed", action="store_true", help="Upload processed files")
    parser.add_argument("--all", action="store_true", help="Upload all files")
    args = parser.parse_args()

    try:
        sync = GoogleDriveSync()
        total = 0
        if args.upload_raw or args.all:
            total += sync.sync_directory(Path("data/raw"), "raw")
        if args.upload_processed or args.all:
            total += sync.sync_directory(Path("data/processed"), "processed")
        if not (args.upload_raw or args.upload_processed or args.all):
            total += sync.sync_directory(Path("data/processed"), "processed")

        logger.info(f"Sync complete! Total files uploaded: {total}")

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
