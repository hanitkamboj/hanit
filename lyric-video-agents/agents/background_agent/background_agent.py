"""
Background Agent - Finds and downloads high-quality, watermark-free background images.
Sources: Unsplash, Pexels, Local assets
"""
import os
import random
from pathlib import Path
from typing import Optional, List, Dict, Any
import requests
from dataclasses import dataclass

from utils import (
    load_config, get_env, ensure_dir, print_agent_header,
    sanitize_filename, logger
)
from models import SongMeta


@dataclass
class BackgroundResult:
    success: bool
    image_path: Optional[str] = None
    source: Optional[str] = None
    error: Optional[str] = None


class BackgroundAgent:
    """Agent responsible for finding and downloading background images."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or load_config()
        self.background_dir = Path(self.config['paths']['background_dir'])
        ensure_dir(self.background_dir)
        
        self.unsplash_key = get_env('UNSPLASH_ACCESS_KEY')
        self.pexels_key = get_env('PEXELS_API_KEY')
        
    def search_unsplash(self, query: str, count: int = 5) -> List[Dict[str, Any]]:
        """Search Unsplash for images."""
        if not self.unsplash_key:
            logger.warning("Unsplash API key not set")
            return []
        
        try:
            url = "https://api.unsplash.com/search/photos"
            headers = {'Authorization': f'Client-ID {self.unsplash_key}'}
            params = {
                'query': query,
                'per_page': count,
                'orientation': 'landscape',
                'content_filter': 'high'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data.get('results', []):
                    results.append({
                        'url': item['urls']['regular'],
                        'download_url': item['links']['download'],
                        'width': item['width'],
                        'height': item['height'],
                        'photographer': item['user']['name'],
                        'source': 'unsplash'
                    })
                return results
        except Exception as e:
            logger.error(f"Unsplash search failed: {e}")
        return []
    
    def search_pexels(self, query: str, count: int = 5) -> List[Dict[str, Any]]:
        """Search Pexels for images."""
        if not self.pexels_key:
            logger.warning("Pexels API key not set")
            return []
        
        try:
            url = "https://api.pexels.com/v1/search"
            headers = {'Authorization': self.pexels_key}
            params = {
                'query': query,
                'per_page': count,
                'orientation': 'landscape',
                'size': 'large'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data.get('photos', []):
                    results.append({
                        'url': item['src']['large'],
                        'download_url': item['src']['original'],
                        'width': item['width'],
                        'height': item['height'],
                        'photographer': item['photographer'],
                        'source': 'pexels'
                    })
                return results
        except Exception as e:
            logger.error(f"Pexels search failed: {e}")
        return []
    
    def get_local_backgrounds(self) -> List[Path]:
        """Get list of local background images."""
        extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp']
        images = []
        for ext in extensions:
            images.extend(self.background_dir.glob(ext))
        return images
    
    def download_image(self, url: str, output_path: Path) -> bool:
        """Download image from URL."""
        try:
            response = requests.get(url, timeout=60, stream=True)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
        except Exception as e:
            logger.error(f"Image download failed: {e}")
        return False
    
    def generate_keywords(self, meta: SongMeta = None, title: str = None, 
                         artist: str = None, genre: str = None) -> List[str]:
        """Generate search keywords based on song metadata."""
        keywords = []
        
        if meta:
            title = title or meta.title
            artist = artist or meta.artist
            genre = genre or meta.genre
        
        # Extract themes from title
        if title:
            # Common themes
            theme_keywords = {
                'love': ['love', 'heart', 'romance', 'couple'],
                'night': ['night', 'dark', 'stars', 'moon', 'city'],
                'dream': ['dream', 'cloud', 'sky', 'fantasy'],
                'sad': ['sad', 'rain', 'alone', 'melancholy'],
                'happy': ['happy', 'sun', 'bright', 'colorful'],
                'fire': ['fire', 'flame', 'hot', 'burn'],
                'water': ['ocean', 'sea', 'water', 'waves'],
            }
            
            title_lower = title.lower()
            for theme, words in theme_keywords.items():
                if any(word in title_lower for word in words):
                    keywords.extend(words[:2])
        
        # Add genre-based keywords
        if genre:
            genre_keywords = {
                'pop': ['colorful', 'vibrant', 'modern'],
                'rock': ['dark', 'edgy', 'urban'],
                'electronic': ['neon', 'abstract', 'futuristic'],
                'acoustic': ['nature', 'warm', 'cozy'],
            }
            for g, words in genre_keywords.items():
                if g in genre.lower():
                    keywords.extend(words)
        
        # Default aesthetic keywords
        if not keywords:
            keywords = ['aesthetic', 'abstract', 'colorful', 'artistic']
        
        # Remove duplicates and limit
        keywords = list(set(keywords))[:5]
        
        return keywords
    
    def process(self, meta: SongMeta = None, title: str = None, 
                artist: str = None, genre: str = None, 
                custom_query: str = None) -> BackgroundResult:
        """
        Main processing function.
        
        Args:
            meta: Song metadata
            title: Song title
            artist: Artist name
            genre: Song genre
            custom_query: Custom search query
            
        Returns:
            BackgroundResult with image path
        """
        print_agent_header("🖼️  BACKGROUND AGENT")
        
        # Check for local backgrounds first
        local_images = self.get_local_backgrounds()
        if local_images:
            logger.info(f"Found {len(local_images)} local background images")
            selected = random.choice(local_images)
            logger.info(f"✓ Using local background: {selected.name}")
            return BackgroundResult(
                success=True,
                image_path=str(selected),
                source="local"
            )
        
        # Generate search keywords
        if custom_query:
            keywords = [custom_query]
        else:
            keywords = self.generate_keywords(meta, title, artist, genre)
        
        logger.info(f"Search keywords: {', '.join(keywords)}")
        
        # Search for images
        all_images = []
        
        # Try Unsplash
        for keyword in keywords[:2]:
            logger.info(f"Searching Unsplash for: {keyword}")
            images = self.search_unsplash(keyword, count=3)
            all_images.extend(images)
        
        # Try Pexels
        if len(all_images) < 3:
            for keyword in keywords[:2]:
                logger.info(f"Searching Pexels for: {keyword}")
                images = self.search_pexels(keyword, count=3)
                all_images.extend(images)
        
        if not all_images:
            return BackgroundResult(
                success=False,
                error="No images found. Please set API keys or add local backgrounds."
            )
        
        # Filter by resolution (min 1920x1080)
        min_width = 1920
        min_height = 1080
        valid_images = [
            img for img in all_images 
            if img['width'] >= min_width and img['height'] >= min_height
        ]
        
        if not valid_images:
            valid_images = all_images  # Use what we have
        
        # Select random image
        selected = random.choice(valid_images)
        
        # Download image
        filename = sanitize_filename(f"bg_{keywords[0]}_{selected['source']}.jpg")
        output_path = self.background_dir / filename
        
        if output_path.exists():
            logger.info(f"Background already exists: {output_path}")
        else:
            logger.info(f"Downloading background from {selected['source']}...")
            success = self.download_image(selected['download_url'], output_path)
            if not success:
                return BackgroundResult(
                    success=False,
                    error="Failed to download background image"
                )
        
        logger.info(f"✓ Background downloaded: {output_path}")
        logger.info(f"  Photographer: {selected.get('photographer', 'Unknown')}")
        
        return BackgroundResult(
            success=True,
            image_path=str(output_path),
            source=selected['source']
        )


def main():
    """Test the background agent."""
    agent = BackgroundAgent()
    
    # Test with keywords
    result = agent.process(
        title="Die With A Smile",
        artist="Lady Gaga",
        genre="pop"
    )
    print(f"\nResult: {result}")


if __name__ == "__main__":
    main()
