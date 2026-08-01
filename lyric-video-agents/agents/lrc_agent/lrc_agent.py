"""
LRC Agent - Finds and parses synchronized lyrics (LRC/SRT) with word-level timing.
Sources: Hanit API (Spotify), LRCLib, Genius.com
"""
import re
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass

from utils import (
    load_config, get_env, ensure_dir, print_agent_header,
    sanitize_filename, parse_timestamp, format_timestamp, logger
)
from models import LyricLine, Word, SongMeta


@dataclass
class LRCResult:
    success: bool
    lyrics: Optional[List[LyricLine]] = None
    lrc_text: Optional[str] = None
    source: Optional[str] = None
    error: Optional[str] = None


class LRCAgent:
    """Agent responsible for finding and parsing synchronized lyrics."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or load_config()
        self.genius_token = get_env('GENIUS_ACCESS_TOKEN')
        
    def get_from_hanit_api(self, spotify_url: str) -> Optional[str]:
        """Fetch synced lyrics from hanit-api using Spotify URL."""
        try:
            api_base = self.config['hanit_api']['base_url']
            url = f"{api_base}/getLyrics?url={spotify_url}"
            
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get('syncedLyrics'):
                    logger.info("✓ Got synced lyrics from Hanit API")
                    return data['syncedLyrics']
                elif data.get('lyrics'):
                    logger.info("Got plain lyrics from Hanit API (no sync)")
                    return self._convert_plain_to_lrc(data['lyrics'])
        except Exception as e:
            logger.error(f"Hanit API failed: {e}")
        return None
    
    def get_from_lrclib(self, title: str, artist: str, duration: float = None) -> Optional[str]:
        """Fetch synced lyrics from lrclib.net."""
        try:
            url = "https://lrclib.net/api/get"
            params = {
                'track_name': title,
                'artist_name': artist,
            }
            if duration:
                params['duration'] = int(duration)
            
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get('syncedLyrics'):
                    logger.info("✓ Got synced lyrics from LRCLib")
                    return data['syncedLyrics']
                elif data.get('plainLyrics'):
                    logger.info("Got plain lyrics from LRCLib (no sync)")
                    return self._convert_plain_to_lrc(data['plainLyrics'])
        except Exception as e:
            logger.error(f"LRCLib failed: {e}")
        return None
    
    def search_lrclib(self, query: str) -> Optional[str]:
        """Search LRCLib for lyrics."""
        try:
            url = "https://lrclib.net/api/search"
            response = requests.get(url, params={'q': query}, timeout=30)
            if response.status_code == 200:
                results = response.json()
                if results:
                    best = results[0]
                    if best.get('syncedLyrics'):
                        logger.info("✓ Found synced lyrics via LRCLib search")
                        return best['syncedLyrics']
                    elif best.get('plainLyrics'):
                        return self._convert_plain_to_lrc(best['plainLyrics'])
        except Exception as e:
            logger.error(f"LRCLib search failed: {e}")
        return None
    
    def get_from_genius(self, title: str, artist: str) -> Optional[str]:
        """Fetch lyrics from Genius.com (plain text, no sync)."""
        try:
            # Search for song
            search_url = "https://api.genius.com/search"
            headers = {'Authorization': f'Bearer {self.genius_token}'} if self.genius_token else {}
            params = {'q': f"{title} {artist}"}
            
            response = requests.get(search_url, params=params, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                hits = data.get('response', {}).get('hits', [])
                if hits:
                    song_url = hits[0]['result']['url']
                    return self._scrape_genius_page(song_url)
        except Exception as e:
            logger.error(f"Genius API failed: {e}")
        return None
    
    def _scrape_genius_page(self, url: str) -> Optional[str]:
        """Scrape lyrics from Genius page."""
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                lyrics_divs = soup.find_all('div', {'data-lyrics-container': 'true'})
                if lyrics_divs:
                    lyrics_text = '\n'.join([div.get_text() for div in lyrics_divs])
                    return self._convert_plain_to_lrc(lyrics_text)
        except Exception as e:
            logger.error(f"Genius scraping failed: {e}")
        return None
    
    def _convert_plain_to_lrc(self, plain_lyrics: str) -> str:
        """Convert plain lyrics to LRC format with estimated timing."""
        lines = plain_lyrics.strip().split('\n')
        lrc_lines = []
        
        # Estimate ~3 seconds per line as default
        time_per_line = 3.0
        current_time = 0.0
        
        for line in lines:
            line = line.strip()
            if line:
                minutes = int(current_time // 60)
                seconds = current_time % 60
                lrc_lines.append(f"[{minutes:02d}:{seconds:05.2f}]{line}")
                current_time += time_per_line
        
        return '\n'.join(lrc_lines)
    
    def parse_lrc(self, lrc_text: str) -> List[LyricLine]:
        """Parse LRC text into structured LyricLine objects with word-level timing."""
        lines = []
        line_id = 0
        
        # LRC timestamp pattern: [mm:ss.xx] or [mm:ss.xxx]
        timestamp_pattern = r'\[(\d{2}:\d{2}(?:\.\d{2,3})?)\]'
        
        # Split into timestamped lines
        raw_lines = lrc_text.strip().split('\n')
        
        for raw_line in raw_lines:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            
            # Find all timestamps in the line
            timestamps = re.findall(timestamp_pattern, raw_line)
            if not timestamps:
                continue
            
            # Remove timestamps to get text
            text = re.sub(timestamp_pattern, '', raw_line).strip()
            if not text:
                continue
            
            # Parse start time
            start_time = parse_timestamp(timestamps[0])
            
            # Create words with estimated timing
            words = self._create_word_timing(text, start_time)
            
            # Estimate end time (next line start or +3 seconds)
            end_time = start_time + 3.0
            
            line = LyricLine(
                id=line_id,
                text=text,
                start_time=start_time,
                end_time=end_time,
                words=words
            )
            lines.append(line)
            line_id += 1
        
        # Update end times based on next line start
        for i in range(len(lines) - 1):
            lines[i].end_time = lines[i + 1].start_time
        
        return lines
    
    def _create_word_timing(self, text: str, line_start: float) -> List[Word]:
        """Create word-level timing by distributing time evenly across words."""
        words_text = text.split()
        if not words_text:
            return []
        
        # Estimate line duration (~0.5s per word, min 1s)
        line_duration = max(1.0, len(words_text) * 0.5)
        time_per_word = line_duration / len(words_text)
        
        words = []
        current_time = line_start
        
        for word_text in words_text:
            word = Word(
                word=word_text,
                start_time=current_time,
                end_time=current_time + time_per_word
            )
            words.append(word)
            current_time += time_per_word
        
        return words
    
    def process(self, meta: SongMeta = None, spotify_url: str = None, 
                title: str = None, artist: str = None) -> LRCResult:
        """
        Main processing function.
        
        Args:
            meta: Song metadata
            spotify_url: Spotify track URL (for hanit-api)
            title: Song title
            artist: Artist name
            
        Returns:
            LRCResult with parsed lyrics
        """
        print_agent_header("📝 LRC AGENT")
        
        # Extract info from meta if provided
        if meta:
            title = title or meta.title
            artist = artist or meta.artist
            spotify_url = spotify_url or meta.spotify_url
        
        if not title or not artist:
            return LRCResult(success=False, error="Title and artist required")
        
        logger.info(f"Searching lyrics for: {title} by {artist}")
        
        lrc_text = None
        source = None
        
        # Try sources in order of preference
        # 1. Hanit API (Spotify synced lyrics)
        if spotify_url:
            logger.info("Trying Hanit API...")
            lrc_text = self.get_from_hanit_api(spotify_url)
            if lrc_text:
                source = "hanit_api"
        
        # 2. LRCLib direct lookup
        if not lrc_text:
            logger.info("Trying LRCLib...")
            duration = meta.duration if meta else None
            lrc_text = self.get_from_lrclib(title, artist, duration)
            if lrc_text:
                source = "lrclib"
        
        # 3. LRCLib search
        if not lrc_text:
            logger.info("Trying LRCLib search...")
            lrc_text = self.search_lrclib(f"{title} {artist}")
            if lrc_text:
                source = "lrclib_search"
        
        # 4. Genius (plain text only)
        if not lrc_text:
            logger.info("Trying Genius...")
            lrc_text = self.get_from_genius(title, artist)
            if lrc_text:
                source = "genius"
        
        if not lrc_text:
            return LRCResult(success=False, error="Could not find lyrics from any source")
        
        # Parse LRC text
        logger.info("Parsing lyrics...")
        lyrics = self.parse_lrc(lrc_text)
        
        logger.info(f"✓ Found {len(lyrics)} lyric lines from {source}")
        
        return LRCResult(
            success=True,
            lyrics=lyrics,
            lrc_text=lrc_text,
            source=source
        )


def main():
    """Test the LRC agent."""
    agent = LRCAgent()
    
    # Test with search
    result = agent.process(title="Die With A Smile", artist="Lady Gaga Bruno Mars")
    print(f"\nResult: {result.success}")
    if result.lyrics:
        print(f"Found {len(result.lyrics)} lines")
        for line in result.lyrics[:3]:
            print(f"  [{format_timestamp(line.start_time)}] {line.text}")


if __name__ == "__main__":
    main()
