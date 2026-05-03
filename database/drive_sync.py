import os
import json
import logging
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io
import asyncio

SCOPES = ['https://www.googleapis.com/auth/drive.file']
DB_NAME = "dating.db"

def get_drive_service():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if not creds_json:
        logging.error("GOOGLE_CREDENTIALS environment variable not found.")
        return None
    
    try:
        creds_info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        logging.error(f"Failed to authenticate with Google Drive: {e}")
        return None

async def download_latest_backup(folder_id):
    service = get_drive_service()
    if not service: return False

    try:
        # Search for any backup files in the folder, sort by modified time
        query = f"'{folder_id}' in parents and name contains '.db' and trashed = false"
        results = await asyncio.to_thread(service.files().list(q=query, orderBy="modifiedTime desc", pageSize=1, fields="files(id, name, modifiedTime)").execute)
        items = results.get('files', [])

        if not items:
            logging.info("No backups found on Google Drive. Starting with an empty database.")
            return False

        latest_file = items[0]
        file_id = latest_file['id']
        file_name = latest_file['name']
        
        logging.info(f"Found latest backup: {file_name} (ID: {file_id}). Downloading...")

        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(DB_NAME, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        
        def download_file():
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                
        await asyncio.to_thread(download_file)
            
        logging.info("Successfully downloaded database backup from Google Drive.")
        return True

    except Exception as e:
        logging.error(f"Error downloading backup: {e}")
        return False

async def upload_backup(folder_id, backup_type="short", index=1):
    """
    backup_type can be 'short' or 'daily'
    index is the number (1-5 for short, 1-3 for daily)
    """
    service = get_drive_service()
    if not service: return False
    
    if not os.path.exists(DB_NAME):
        logging.error(f"Cannot upload backup: {DB_NAME} does not exist locally.")
        return False

    file_name = f"backup_{index}.db" if backup_type == "short" else f"daily_{index}.db"

    try:
        # Check if the file already exists in the folder
        query = f"'{folder_id}' in parents and name = '{file_name}' and trashed = false"
        results = await asyncio.to_thread(service.files().list(q=query, spaces='drive', fields='files(id, name)').execute)
        items = results.get('files', [])

        file_metadata = {'name': file_name}
        media = MediaFileUpload(DB_NAME, mimetype='application/x-sqlite3', resumable=True)

        if items:
            # Update existing file
            file_id = items[0]['id']
            await asyncio.to_thread(service.files().update(fileId=file_id, media_body=media).execute)
            logging.info(f"Updated existing Google Drive backup: {file_name}")
        else:
            # Create new file
            file_metadata['parents'] = [folder_id]
            await asyncio.to_thread(service.files().create(body=file_metadata, media_body=media, fields='id').execute)
            logging.info(f"Created new Google Drive backup: {file_name}")
            
        return True

    except Exception as e:
        logging.error(f"Error uploading backup {file_name}: {e}")
        return False
