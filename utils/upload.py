import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import google.oauth2.credentials
import json
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

load_dotenv()

# YouTube API configuration
CLIENT_SECRETS_FILE = os.getenv("YT_CLIENT_SECRETS_FILE", "client_secret.json")
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

logger = logging.getLogger(__name__)

def get_authenticated_service():
    credentials = None
    if os.path.exists("yt_credentials.json"):
        with open("yt_credentials.json", "r") as f:
            data = json.load(f)
            credentials = google.oauth2.credentials.Credentials(
                token=data.get('token'),
                refresh_token=data.get('refresh_token'),
                token_uri=data.get('token_uri'),
                client_id=data.get('client_id'),
                client_secret=data.get('client_secret'),
                scopes=SCOPES
            )

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES
            )
            credentials = flow.run_local_server(port=0)

        with open("yt_credentials.json", "w") as f:
            json.dump({
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }, f)

    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

def upload_short_to_youtube(
    video_path: Path, 
    title: str, 
    description: str = "",
) -> str:
    """
    Uploads a YouTube Short (vertical video ≤60s).
    Returns the URL of the uploaded Short.
    """
    try:
        youtube = get_authenticated_service()
        
        media = MediaFileUpload(
            filename=str(video_path),
            mimetype="video/mp4",
            resumable=True
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "categoryId": "22",  # People & Blogs
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False,
                    "madeForKids": False,
                    "publishAt": None,  # Optional: schedule if needed
                },
                # Shorts-specific metadata
                "contentDetails": {
                    "durationMs": "60000",  # Max 60 seconds
                    "dimension": "vertical",  # 9:16 aspect ratio
                    "definition": "hd",  # 720p or 1080p
                },
                "recordingDetails": {
                    "recordingType": "short",  # Mark as Short
                }
            },
            media_body=media
        )

        response = request.execute()
        video_id = response.get("id")
        short_url = f"https://youtube.com/shorts/{video_id}"

        logger.info(f"✅ Short uploaded: {short_url}")
        return short_url

    except Exception as e:
        logger.error(f"❌ Short upload failed: {e}")
        raise