"""
Main Orchestrator - Coordinates all agents to produce a complete lyric video
with SEO metadata, ready for YouTube upload.

Usage:
    python pipeline.py --query "Song Name Artist"
    python pipeline.py --spotify-url "https://open.spotify.com/track/..."
    python pipeline.py --title "Song" --artist "Artist"
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Ensure imports work from project root
sys.path.insert(0, str(Path(__file__).parent))

from utils import (
    load_config, print_agent_header, ensure_dir, logger,
    cleanup_temp_files, sanitize_filename
)
from models import SongData, PipelineResult, SEOData
from agents.audio_agent import AudioAgent
from agents.lrc_agent import LRCAgent
from agents.background_agent import BackgroundAgent
from agents.video_generator import VideoGeneratorAgent
from agents.seo_agent import SEOAgent
from agents.youtube_uploader import YouTubeUploaderAgent


class LyricVideoPipeline:
    """Coordinates all agents to produce a complete lyric video."""

    def __init__(self, config: dict = None):
        self.config = config or load_config()
        self.audio_agent = AudioAgent(self.config)
        self.lrc_agent = LRCAgent(self.config)
        self.background_agent = BackgroundAgent(self.config)
        self.video_generator = VideoGeneratorAgent(self.config)
        self.seo_agent = SEOAgent(self.config)
        self.youtube_uploader = YouTubeUploaderAgent(self.config)

    def run(self, query: str = None, spotify_url: str = None,
            title: str = None, artist: str = None,
            custom_query: str = None, auto_upload: bool = None) -> PipelineResult:
        """Run the full pipeline."""
        # Generate query from title+artist if not provided
        if not query and not spotify_url and title and artist:
            query = f"{title} {artist}"
        
        if not query and not spotify_url:
            return PipelineResult(success=False, error="Provide --query, --spotify-url, or --title + --artist")
        
        print_agent_header("🎬 LYRIC VIDEO PIPELINE", "=" * 60)
        logger.info("Starting lyric video generation pipeline")

        # Step 1: Audio Agent
        logger.info("STEP 1/5: Finding audio...")
        audio_result = self.audio_agent.process(
            query=query,
            spotify_url=spotify_url
        )
        if not audio_result.success:
            return PipelineResult(success=False, error=audio_result.error)
        audio_path = audio_result.audio_path
        meta = audio_result.meta

        # Step 2: LRC Agent
        logger.info("STEP 2/5: Finding lyrics...")
        lrc_result = self.lrc_agent.process(
            meta=meta,
            spotify_url=spotify_url,
            title=title or meta.title,
            artist=artist or meta.artist
        )
        if not lrc_result.success:
            return PipelineResult(success=False, error=lrc_result.error)
        lyrics = lrc_result.lyrics
        lrc_text = lrc_result.lrc_text

        # Step 3: Background Agent
        logger.info("STEP 3/5: Finding background...")
        bg_result = self.background_agent.process(
            meta=meta,
            title=meta.title,
            artist=meta.artist,
            custom_query=custom_query
        )
        if not bg_result.success:
            return PipelineResult(success=False, error=bg_result.error)
        background_path = bg_result.image_path

        # Step 4: Video Generator
        logger.info("STEP 4/5: Generating video...")
        video_result = self.video_generator.process(
            audio_path=audio_path,
            lyrics=lyrics,
            background_path=background_path,
            meta=meta
        )
        if not video_result.success:
            return PipelineResult(success=False, error=video_result.error)
        video_path = video_result.video_path

        # Step 5: SEO Agent
        logger.info("STEP 5/5: Generating SEO metadata...")
        seo_result = self.seo_agent.process(meta=meta, lines=lyrics)
        if not seo_result.success:
            return PipelineResult(success=False, error=seo_result.error)
        seo_data = seo_result.seo_data

        # Save SEO metadata to JSON for reuse
        self._save_seo(seo_data, meta)
        # Save lyrics JSON for reuse
        self._save_lyrics(lyrics, meta)

        # Optional: YouTube Upload
        if auto_upload is not None and auto_upload:
            logger.info("Uploading to YouTube...")
            upload_result = self.youtube_uploader.process(
                video_path=video_path,
                seo_data=seo_data,
                auto_upload=True
            )
            if not upload_result.success:
                logger.warning(f"Upload failed: {upload_result.error}")
            else:
                logger.info(f"Video uploaded: {upload_result.video_url}")

        logger.info("✓ Pipeline completed successfully!")
        return PipelineResult(
            success=True,
            video_path=video_path,
            seo_data=seo_data,
            song_data=SongData(
                meta=meta,
                lyrics=lyrics,
                audio_path=audio_path,
                background_path=background_path
            )
        )

    def _save_seo(self, seo_data: SEOData, meta):
        """Save SEO metadata to JSON file."""
        try:
            out_dir = Path(self.config['paths']['output_dir'])
            ensure_dir(out_dir)
            filename = sanitize_filename(f"{meta.artist} - {meta.title}_seo.json")
            path = out_dir / filename
            with open(path, 'w') as f:
                json.dump({
                    'title': seo_data.title,
                    'description': seo_data.description,
                    'tags': seo_data.tags,
                    'hashtags': seo_data.hashtags,
                    'timestamps': seo_data.timestamps,
                }, f, indent=2)
            logger.info(f"SEO metadata saved: {path}")
        except Exception as e:
            logger.error(f"Failed to save SEO: {e}")

    def _save_lyrics(self, lyrics, meta):
        """Save lyrics to JSON file for reuse."""
        try:
            out_dir = Path(self.config['paths']['output_dir'])
            ensure_dir(out_dir)
            filename = sanitize_filename(f"{meta.artist} - {meta.title}_lyrics.json")
            path = out_dir / filename
            with open(path, 'w') as f:
                json.dump([
                    {
                        'id': line.id,
                        'text': line.text,
                        'start_time': line.start_time,
                        'end_time': line.end_time,
                    }
                    for line in lyrics
                ], f, indent=2, default=str)
            logger.info(f"Lyrics saved: {path}")
        except Exception as e:
            logger.error(f"Failed to save lyrics: {e}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Lyric Video Pipeline - generates lyric videos with SEO metadata'
    )
    parser.add_argument('--query', help='Song search query (e.g., "Lady Gaga Die With A Smile")')
    parser.add_argument('--spotify-url', help='Spotify track URL')
    parser.add_argument('--title', help='Song title')
    parser.add_argument('--artist', help='Artist name')
    parser.add_argument('--custom-query', help='Custom background image query')
    parser.add_argument('--auto-upload', action='store_true', help='Auto-upload to YouTube')
    parser.add_argument('--upload', action='store_true', help='Upload to YouTube after generation')

    args = parser.parse_args()

    # Validate inputs
    if not any([args.query, args.spotify_url, (args.title and args.artist)]):
        parser.error('Provide --query, --spotify-url, or --title + --artist')

    pipeline = LyricVideoPipeline()
    result = pipeline.run(
        query=args.query,
        spotify_url=args.spotify_url,
        title=args.title,
        artist=args.artist,
        custom_query=args.custom_query,
        auto_upload=args.upload or args.auto_upload
    )

    if result.success:
        print("\n" + "=" * 60)
        print("✅ PIPELINE COMPLETED")
        print(f"🎬 Video: {result.video_path}")
        print(f"🏷️ Title: {result.seo_data.title}")
        if result.seo_data and result.seo_data.title:
            print("📄 SEO metadata saved alongside video")
        print("=" * 60)
    else:
        print("\n❌ Pipeline failed:")
        print(f"   {result.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
