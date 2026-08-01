"""
YouTube Uploader Agent - Uploads videos to YouTube with metadata.
Uses YouTube Data API v3 for authentication and upload.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from models import SEOData
from utils import (
    load_config, get_env, print_agent_header, 
    ensure_dir, logger
)


# YouTube API scopes
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']


@dataclass
class UploadResult:
    success: bool
    video_id: Optional[str] = None
    video_url: Optional[str] = None
    error: Optional[str] = None


class YouTubeUploaderAgent:
    """Agent responsible for uploading videos to YouTube."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or load_config()
        self.client_secrets_file = self.config['api'].get('youtube_client_secrets', 'client_secrets.json')
        self.credentials_file = 'token.json'
        
        self.youtube_cfg = self.config['youtube']
        self.category_id = self.youtube_cfg['category']
        self.privacy_status = self.youtube_cfg['privacy_status']
        
    def get_credentials(self) -> Credentials:
        """Get or refresh YouTube API credentials."""
        creds = None
        
        # Load existing credentials
        if os.path.exists(self.credentials_file):
            creds = Credentials.from_authorized_user_file(self.credentials_file, SCOPES)
        
        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.client_secrets_file):
                    raise FileNotFoundError(
                        f"Client secrets file not found: {self.client_secrets_file}\n"
                        "Please download it from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials
            with open(self.credentials_file, 'w') as token:
                token.write(creds.to_json())
        
        return creds
    
    def build_service(self):
        """Build YouTube API service."""
        creds = self.get_credentials()
        return build('youtube', 'v3', credentials=creds)
    
    def upload_video(self, video_path: str, seo_data: SEOData, 
                    thumbnail_path: str = None) -> UploadResult:
        """
        Upload video to YouTube.
        
        Args:
            video_path: Path to video file
            seo_data: SEO metadata
            thumbnail_path: Optional thumbnail image path
            
        Returns:
            UploadResult with video ID and URL
        """
        print_agent_header("📺 YOUTUBE UPLOADER AGENT")
        
        try:
            logger.info("Initializing YouTube API...")
            youtube = self.build_service()
            
            # Prepare video metadata
            body = {
                'snippet': {
                    'title': seo_data.title,
                    'description': seo_data.description,
                    'tags': seo_data.tags,
                    'categoryId': self.category_id,
                },
                'status': {
                    'privacyStatus': self.privacy_status,
                    'selfDeclaredMadeForKids': False,
                }
            }
            
            # Upload video
            logger.info(f"Uploading video: {video_path}")
            media = MediaFileUpload(
                video_path,
                mimetype='video/mp4',
                resumable=True,
                chunksize=1024*1024*10  # 10MB chunks
            )
            
            request = youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"Upload progress: {int(status.progress() * 100)}%")
            
            video_id = response['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            logger.info(f"✓ Video uploaded successfully!")
            logger.info(f"Video ID: {video_id}")
            logger.info(f"Video URL: {video_url}")
            
            # Upload thumbnail if provided
            if thumbnail_path and os.path.exists(thumbnail_path):
                self._upload_thumbnail(youtube, video_id, thumbnail_path)
            
            return UploadResult(
                success=True,
                video_id=video_id,
                video_url=video_url
            )
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return UploadResult(success=False, error=str(e))
    
    def _upload_thumbnail(self, youtube, video_id: str, thumbnail_path: str):
        """Upload custom thumbnail for video."""
        try:
            logger.info(f"Uploading thumbnail: {thumbnail_path}")
            
            media = MediaFileUpload(
                thumbnail_path,
                mimetype='image/jpeg',
                resumable=True
            )
            
            request = youtube.thumbnails().set(
                videoId=video_id,
                media_body=media
            )
            
            response = request.execute()
            logger.info("✓ Thumbnail uploaded successfully")
            
        except Exception as e:
            logger.error(f"Thumbnail upload failed: {e}")
    
    def process(self, video_path: str, seo_data: SEOData,
                thumbnail_path: str = None, auto_upload: bool = None) -> UploadResult:
        """
        Main processing function.
        
        Args:
            video_path: Path to video file
            seo_data: SEO metadata
            thumbnail_path: Optional thumbnail path
            auto_upload: Override config auto_upload setting
            
        Returns:
            UploadResult with video ID and URL
        """
        # Check if auto-upload is enabled
        should_upload = auto_upload if auto_upload is not None else self.youtube_cfg.get('auto_upload', False)
        
        if not should_upload:
            logger.info("Auto-upload is disabled. Skipping upload.")
            return UploadResult(
                success=True,
                video_id=None,
                video_url=None
            )
        
        return self.upload_video(video_path, seo_data, thumbnail_path)


def main():
    """Test the YouTube uploader."""
    print("YouTube Uploader Agent - Ready")
    print("Note: Requires client_secrets.json for authentication")
    print("Download from: https://console.cloud.google.com/apis/credentials")


if __name__ == "__main__":
    main()
