"""
SEO Agent - Generates optimized YouTube metadata (title, description, tags, hashtags).
Follows TheCloudLyric channel format and YouTube SEO best practices.
"""
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup

from models import SongMeta, LyricLine, SEOData
from utils import (
    load_config, get_env, print_agent_header, 
    format_timestamp, sanitize_filename, logger
)


@dataclass
class SEOResult:
    success: bool
    seo_data: Optional[SEOData] = None
    error: Optional[str] = None


class SEOAgent:
    """Agent responsible for generating YouTube SEO metadata."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or load_config()
        
    def generate_title(self, meta: SongMeta) -> str:
        """Generate optimized video title."""
        # Format: "Artist - Song Title (Lyrics)"
        return f"{meta.artist} - {meta.title} (Lyrics)"
    
    def generate_timestamps(self, lines: List[LyricLine]) -> Dict[str, str]:
        """Generate timestamps from lyric lines."""
        timestamps = {}
        
        # Find section markers in lyrics
        section_keywords = {
            'intro': ['intro', 'introduction'],
            'verse': ['verse 1', 'verse 2', 'verse 3', 'verse'],
            'pre-chorus': ['pre-chorus', 'pre chorus'],
            'chorus': ['chorus'],
            'bridge': ['bridge'],
            'outro': ['outro', 'ending'],
            'post-chorus': ['post-chorus', 'post chorus'],
            'hook': ['hook'],
            'instrumental': ['instrumental', 'break']
        }
        
        for line in lines:
            text_lower = line.text.lower()
            
            # Check for section markers
            for section, keywords in section_keywords.items():
                if any(keyword in text_lower for keyword in keywords):
                    timestamp = format_timestamp(line.start_time)
                    section_name = section.replace('-', ' ').title()
                    
                    # Avoid duplicates
                    if section_name not in timestamps:
                        timestamps[section_name] = timestamp
                        break
        
        # If no sections found, create basic timestamps
        if not timestamps and lines:
            timestamps['Start'] = format_timestamp(lines[0].start_time)
            if len(lines) > 1:
                timestamps['Middle'] = format_timestamp(lines[len(lines)//2].start_time)
            timestamps['End'] = format_timestamp(lines[-1].start_time)
        
        return timestamps
    
    def format_lyrics_for_description(self, lines: List[LyricLine]) -> str:
        """Format lyrics for YouTube description."""
        lyrics_text = []
        
        for line in lines:
            # Clean up the text
            text = line.text.strip()
            if text:
                lyrics_text.append(text)
        
        return '\n\n'.join(lyrics_text)
    
    def generate_description(self, meta: SongMeta, lines: List[LyricLine],
                           timestamps: Dict[str, str]) -> str:
        """Generate optimized video description."""
        description_parts = []
        
        # Header
        description_parts.append(f"{meta.artist} - {meta.title} (Lyrics)")
        description_parts.append("")
        
        # Intro text
        description_parts.append(
            f"🎵 Enjoy the lyric video for \"{meta.title}\" by {meta.artist}"
        )
        if meta.album:
            description_parts.append(
                f" — featured on the {meta.album} album."
            )
        description_parts.append("")
        description_parts.append(
            "Full lyrics on screen throughout — perfect for singing along, "
            "learning the words, or just vibing to the music."
        )
        description_parts.append("")
        
        # Song info
        description_parts.append(f"🎧 Song: {meta.title}")
        description_parts.append(f"🎤 Artist{'s' if ', ' in meta.artist else ''}: {meta.artist}")
        if meta.release_date:
            description_parts.append(f"📅 Released: {meta.release_date}")
        if meta.album:
            description_parts.append(f"💿 Album: {meta.album}")
        if meta.genre:
            description_parts.append(f"🎹 Genre: {meta.genre}")
        if meta.label:
            description_parts.append(f"🏷️ Label: {meta.label}")
        description_parts.append("")
        
        # Lyrics section
        description_parts.append("LYRICS:")
        description_parts.append("")
        description_parts.append(self.format_lyrics_for_description(lines))
        description_parts.append("")
        description_parts.append("")
        
        # Timestamps
        if timestamps:
            description_parts.append("⏱️ TIMESTAMPS")
            for section, timestamp in timestamps.items():
                description_parts.append(f"{timestamp} {section}")
            description_parts.append("")
        
        # Call to action
        description_parts.append(
            f"👍 If you enjoyed this lyric video, leave a like and subscribe "
            f"for more lyrics videos from {meta.artist} and similar artists!"
        )
        description_parts.append(
            "🔔 Turn on notifications so you don't miss the next upload."
        )
        description_parts.append(
            "💬 Drop your favorite line from the song in the comments below."
        )
        description_parts.append("")
        
        # Social links
        description_parts.append("📲 Follow us:")
        description_parts.append("Instagram: https://www.instagram.com/_.h.a.rsh._/")
        description_parts.append("")
        
        # Disclaimer
        description_parts.append(
            f"⚠️ This is a fan-made lyrics video created for entertainment purposes. "
            f"All rights to \"{meta.title}\" belong to {meta.artist}."
        )
        description_parts.append("")
        
        # Hashtags (will be added separately)
        
        return '\n'.join(description_parts)
    
    def generate_tags(self, meta: SongMeta) -> List[str]:
        """Generate optimized video tags."""
        tags = []
        
        # Basic tags
        tags.append(meta.artist)
        tags.append(meta.title)
        tags.append(f"{meta.artist} {meta.title}")
        tags.append(f"{meta.title} lyrics")
        tags.append(f"{meta.artist} lyrics")
        tags.append(f"{meta.title} lyric video")
        
        # Variations
        tags.append(f"{meta.artist} {meta.title} lyrics")
        tags.append(f"{meta.title} official lyrics")
        tags.append(f"{meta.title} song lyrics")
        
        # Album/genre tags
        if meta.album:
            tags.append(f"{meta.album} album")
            tags.append(f"{meta.artist} {meta.album}")
        
        if meta.genre:
            tags.append(f"{meta.genre} lyrics")
            tags.append(f"{meta.genre} music")
        
        # Related searches
        tags.append(f"{meta.artist} new song")
        tags.append(f"{meta.title} audio")
        tags.append(f"{meta.title} karaoke")
        tags.append("lyrics video")
        tags.append("lyric video")
        tags.append("song lyrics")
        
        # Limit to 30 tags (YouTube limit)
        return tags[:30]
    
    def generate_hashtags(self, meta: SongMeta) -> List[str]:
        """Generate hashtags for description."""
        hashtags = []
        
        # Artist and song hashtags
        artist_words = meta.artist.replace(' ', '').replace('&', '').replace(',', '')
        hashtags.append(f"#{artist_words}")
        
        title_words = meta.title.replace(' ', '')
        hashtags.append(f"#{title_words}")
        
        # Genre hashtags
        if meta.genre:
            hashtags.append(f"#{meta.genre.replace(' ', '')}")
        
        # Common hashtags
        hashtags.append("#Lyrics")
        hashtags.append("#LyricVideo")
        hashtags.append("#Music")
        
        return hashtags[:15]  # Limit hashtags
    
    def search_song_info(self, title: str, artist: str) -> Dict[str, str]:
        """Search for additional song information."""
        info = {}
        
        try:
            # Search for song on music databases
            query = f"{title} {artist} release date genre"
            # This is a placeholder - in production, you'd use actual APIs
            # like Spotify API, Last.fm, or MusicBrainz
            
        except Exception as e:
            logger.error(f"Song info search failed: {e}")
        
        return info
    
    def process(self, meta: SongMeta, lines: List[LyricLine]) -> SEOResult:
        """
        Main processing function.
        
        Args:
            meta: Song metadata
            lines: List of LyricLine objects
            
        Returns:
            SEOResult with SEO data
        """
        print_agent_header("🔍 SEO AGENT")
        
        try:
            # Generate title
            logger.info("Generating title...")
            title = self.generate_title(meta)
            logger.info(f"Title: {title}")
            
            # Generate timestamps
            logger.info("Generating timestamps...")
            timestamps = self.generate_timestamps(lines)
            logger.info(f"Generated {len(timestamps)} timestamps")
            
            # Generate description
            logger.info("Generating description...")
            description = self.generate_description(meta, lines, timestamps)
            
            # Add hashtags to description
            hashtags = self.generate_hashtags(meta)
            description += '\n' + ' '.join(hashtags)
            
            # Generate tags
            logger.info("Generating tags...")
            tags = self.generate_tags(meta)
            logger.info(f"Generated {len(tags)} tags")
            
            # Create SEO data
            seo_data = SEOData(
                title=title,
                description=description,
                tags=tags,
                hashtags=hashtags,
                timestamps=timestamps
            )
            
            logger.info("✓ SEO metadata generated successfully")
            
            return SEOResult(success=True, seo_data=seo_data)
            
        except Exception as e:
            logger.error(f"SEO generation failed: {e}")
            return SEOResult(success=False, error=str(e))


def main():
    """Test the SEO agent."""
    from models import SongMeta, LyricLine, Word
    
    # Test data
    meta = SongMeta(
        title="Die With A Smile",
        artist="Lady Gaga & Bruno Mars",
        album="Mayhem",
        release_date="August 16, 2024",
        genre="Pop"
    )
    
    lines = [
        LyricLine(id=0, text="I just woke up from a dream", start_time=10.0, words=[]),
        LyricLine(id=1, text="Where you and I had to say goodbye", start_time=15.0, words=[]),
    ]
    
    agent = SEOAgent()
    result = agent.process(meta, lines)
    
    if result.success:
        print(f"\nTitle: {result.seo_data.title}")
        print(f"\nDescription preview:\n{result.seo_data.description[:500]}...")
        print(f"\nTags: {', '.join(result.seo_data.tags[:10])}")
        print(f"\nHashtags: {' '.join(result.seo_data.hashtags)}")


if __name__ == "__main__":
    main()
