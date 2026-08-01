"""
Audio Agent - Finds and downloads high-quality audio for lyric videos.
Sources: YouTube (via yt-dlp), Spotify metadata
"""
import os
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import requests
from dataclasses import dataclass

from utils import (
    load_config, get_env, ensure_dir, print_agent_header,
    sanitize_filename, get_temp_dir, logger
)
from models import SongMeta


@dataclass
class AudioResult:
    success: bool
    audio_path: Optional[str] = None
    meta: Optional[SongMeta] = None
    error: Optional[str] = None


class AudioAgent:
    """Agent responsible for finding and downloading audio files."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or load_config()
        self.audio_dir = Path(self.config['paths']['audio_dir'])
        ensure_dir(self.audio_dir)
        self.temp_dir = get_temp_dir()
        
    def search_youtube(self, query: str) -> Optional[str]:
        """Search YouTube and return best video URL."""
        try:
            search_query = f"ytsearch1:{query} official audio"
            result = subprocess.run(
                ['yt-dlp', '--get-url', '--no-playlist', search_query],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception as e:
            logger.error(f"YouTube search failed: {e}")
        return None
    
    def get_spotify_metadata(self, spotify_url: str) -> Optional[Dict[str, Any]]:
        """Fetch metadata from Spotify URL using hanit-api."""
        try:
            api_base = self.config['hanit_api']['base_url']
            endpoint = self.config['hanit_api']['get_song_data']
            url = f"{api_base}{endpoint}?url={spotify_url}"
            
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Spotify metadata fetch failed: {e}")
        return None
    
    def download_audio(self, url: str, output_path: Path, quality: str = "best") -> bool:
        """Download audio from URL using yt-dlp."""
        try:
            quality_map = {
                "best": "bestaudio[ext=m4a]/bestaudio",
                "high": "bestaudio[ext=m4a]/bestaudio",
                "medium": "bestaudio[ext=m4a]/bestaudio"
            }
            
            format_str = quality_map.get(quality, quality_map["best"])
            
            cmd = [
                'yt-dlp',
                '--format', format_str,
                '--extract-audio',
                '--audio-format', 'm4a',
                '--audio-quality', '0',
                '--output', str(output_path),
                '--no-playlist',
                '--no-check-certificates',
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return True
            else:
                logger.error(f"yt-dlp error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Download timed out")
            return False
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False
    
    def extract_metadata_from_ytdlp(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract metadata from YouTube video."""
        try:
            cmd = [
                'yt-dlp',
                '--dump-json',
                '--no-download',
                '--no-playlist',
                url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
        return None
    
    def process(self, query: str = None, spotify_url: str = None, youtube_url: str = None) -> AudioResult:
        """
        Main processing function.
        
        Args:
            query: Song name to search (e.g., "Lady Gaga Die With A Smile")
            spotify_url: Spotify track URL
            youtube_url: Direct YouTube URL
            
        Returns:
            AudioResult with audio path and metadata
        """
        print_agent_header("🎵 AUDIO AGENT")
        
        meta = None
        audio_url = None
        filename = None
        
        # If Spotify URL provided, get metadata first
        if spotify_url:
            logger.info(f"Fetching Spotify metadata: {spotify_url}")
            spotify_data = self.get_spotify_metadata(spotify_url)
            if spotify_data:
                meta = SongMeta(
                    title=spotify_data.get('name', ''),
                    artist=spotify_data.get('artists', [{}])[0].get('name', ''),
                    album=spotify_data.get('album', {}).get('name', ''),
                    duration=spotify_data.get('duration_ms', 0) / 1000,
                    spotify_url=spotify_url,
                    cover_url=spotify_data.get('album', {}).get('images', [{}])[0].get('url')
                )
                query = f"{meta.title} {meta.artist}"
                logger.info(f"Found: {meta.title} by {meta.artist}")
        
        # Determine audio URL
        if youtube_url:
            audio_url = youtube_url
            logger.info(f"Using provided YouTube URL")
        elif query:
            logger.info(f"Searching YouTube for: {query}")
            audio_url = self.search_youtube(query)
            if not audio_url:
                return AudioResult(success=False, error="Could not find audio on YouTube")
        else:
            return AudioResult(success=False, error="No query or URL provided")
        
        # Extract metadata if not already set
        if not meta and audio_url:
            logger.info("Extracting metadata from YouTube...")
            yt_meta = self.extract_metadata_from_ytdlp(audio_url)
            if yt_meta:
                meta = SongMeta(
                    title=yt_meta.get('title', 'Unknown'),
                    artist=yt_meta.get('uploader', 'Unknown'),
                    duration=yt_meta.get('duration', 0)
                )
        
        # Download audio
        if not meta:
            meta = SongMeta(title="Unknown", artist="Unknown")
        
        filename = sanitize_filename(f"{meta.artist} - {meta.title}.m4a")
        output_path = self.audio_dir / filename
        
        if output_path.exists():
            logger.info(f"Audio already exists: {output_path}")
            return AudioResult(success=True, audio_path=str(output_path), meta=meta)
        
        logger.info(f"Downloading audio to: {output_path}")
        success = self.download_audio(audio_url, output_path)
        
        if success and output_path.exists():
            logger.info(f"✓ Audio downloaded successfully: {output_path}")
            return AudioResult(success=True, audio_path=str(output_path), meta=meta)
        else:
            return AudioResult(success=False, error="Failed to download audio")


def main():
    """Test the audio agent."""
    agent = AudioAgent()
    
    # Test with query
    result = agent.process(query="Lady Gaga Bruno Mars Die With A Smile")
    print(f"\nResult: {result}")


if __name__ == "__main__":
    main()
