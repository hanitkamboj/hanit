"""
Video Generator Agent - Creates smooth lyric videos from audio, lyrics, and background.
Uses moviepy for video encoding and custom renderer for frame generation.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from tqdm import tqdm

from moviepy import AudioFileClip, ImageSequenceClip, CompositeVideoClip, concatenate_videoclips
from moviepy.video.fx import FadeIn, FadeOut

from models import (
    LyricLine, SongMeta, FontSettings, AnimationSettings, 
    VideoSettings, Resolution
)
from utils import (
    load_config, ensure_dir, print_agent_header, 
    sanitize_filename, logger, get_temp_dir
)
from .renderer import VideoRenderer


@dataclass
class VideoResult:
    success: bool
    video_path: Optional[str] = None
    duration: Optional[float] = None
    error: Optional[str] = None


class VideoGeneratorAgent:
    """Agent responsible for generating smooth lyric videos."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or load_config()
        self.output_dir = Path(self.config['paths']['output_dir'])
        self.temp_dir = get_temp_dir()
        ensure_dir(self.output_dir)
        
        # Initialize settings from config
        video_cfg = self.config['video']
        font_cfg = self.config['font']
        anim_cfg = self.config['animation']
        
        self.video_settings = VideoSettings(
            resolution=Resolution(video_cfg['resolution']),
            fps=video_cfg['fps'],
            codec=video_cfg['codec'],
            audio_codec=video_cfg['audio_codec'],
            bitrate=video_cfg['bitrate'],
            preset=video_cfg['preset']
        )
        
        self.font_settings = FontSettings(
            family=font_cfg['family'],
            path=font_cfg['path'],
            size=font_cfg['size'],
            color=font_cfg['color'],
            highlight_color=font_cfg['highlight_color'],
            shadow_color=font_cfg['shadow_color'],
            shadow_offset=font_cfg['shadow_offset'],
            shadow_blur=font_cfg['shadow_blur']
        )
        
        self.anim_settings = AnimationSettings(
            scroll_speed=anim_cfg['scroll_speed'],
            active_line_scale=anim_cfg['active_line_scale'],
            inactive_line_scale=anim_cfg['inactive_line_scale'],
            inactive_opacity=anim_cfg['inactive_opacity'],
            blur_amount=anim_cfg['blur_amount'],
            transition_duration=anim_cfg['transition_duration']
        )
        
        # Initialize renderer
        self.renderer = VideoRenderer(
            self.font_settings,
            self.anim_settings,
            self.video_settings
        )
    
    def generate_frames(self, background_path: str, lines: List[LyricLine],
                       duration: float, fps: int) -> List[str]:
        """Generate all video frames."""
        logger.info(f"Generating {int(duration * fps)} frames at {fps}fps...")
        
        # Create background
        background = self.renderer.create_background(background_path)
        
        # Generate frames
        frames_dir = self.temp_dir / "frames"
        ensure_dir(frames_dir)
        
        frame_paths = []
        total_frames = int(duration * fps)
        
        for frame_idx in tqdm(range(total_frames), desc="Rendering frames"):
            timestamp = frame_idx / fps
            
            # Render frame
            frame = self.renderer.render_frame(background, lines, timestamp)
            
            # Save frame
            frame_path = frames_dir / f"frame_{frame_idx:06d}.png"
            frame.save(frame_path, 'PNG', optimize=False)
            frame_paths.append(str(frame_path))
        
        logger.info(f"✓ Generated {len(frame_paths)} frames")
        return frame_paths
    
    def create_video(self, frame_paths: List[str], audio_path: str, 
                    output_path: Path, fps: int) -> bool:
        """Create final video from frames and audio."""
        try:
            logger.info("Creating video with moviepy...")
            
            # Create video clip from frames
            video_clip = ImageSequenceClip(frame_paths, fps=fps)
            
            # Load audio
            audio_clip = AudioFileClip(audio_path)
            
            # Set audio
            video_clip = video_clip.with_audio(audio_clip)
            
            # Add fade effects
            video_clip = video_clip.with_effects([FadeIn(1.0), FadeOut(2.0)])
            
            # Write video file
            logger.info(f"Encoding video to: {output_path}")
            video_clip.write_videofile(
                str(output_path),
                fps=fps,
                codec=self.video_settings.codec,
                audio_codec=self.video_settings.audio_codec,
                bitrate=self.video_settings.bitrate,
                preset=self.video_settings.preset,
                threads=4,
                logger=None
            )
            
            # Cleanup
            video_clip.close()
            audio_clip.close()
            
            logger.info(f"✓ Video created successfully: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Video creation failed: {e}")
            return False
    
    def cleanup_frames(self, frame_paths: List[str]):
        """Clean up temporary frame files."""
        import shutil
        frames_dir = self.temp_dir / "frames"
        if frames_dir.exists():
            shutil.rmtree(frames_dir)
    
    def process(self, audio_path: str, lyrics: List[LyricLine], 
                background_path: str, meta: SongMeta = None) -> VideoResult:
        """
        Main processing function.
        
        Args:
            audio_path: Path to audio file
            lyrics: List of LyricLine objects
            background_path: Path to background image
            meta: Song metadata
            
        Returns:
            VideoResult with output video path
        """
        print_agent_header("🎬 VIDEO GENERATOR AGENT")
        
        # Get audio duration
        try:
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            audio_clip.close()
        except Exception as e:
            return VideoResult(success=False, error=f"Could not read audio: {e}")
        
        logger.info(f"Audio duration: {duration:.2f}s")
        
        # Generate output filename
        if meta:
            filename = sanitize_filename(f"{meta.artist} - {meta.title} (Lyrics).mp4")
        else:
            filename = "lyric_video.mp4"
        
        output_path = self.output_dir / filename
        
        # Check if already exists
        if output_path.exists():
            logger.info(f"Video already exists: {output_path}")
            return VideoResult(
                success=True,
                video_path=str(output_path),
                duration=duration
            )
        
        # Generate frames
        frame_paths = self.generate_frames(
            background_path,
            lyrics,
            duration,
            self.video_settings.fps
        )
        
        if not frame_paths:
            return VideoResult(success=False, error="Failed to generate frames")
        
        # Create video
        success = self.create_video(
            frame_paths,
            audio_path,
            output_path,
            self.video_settings.fps
        )
        
        # Cleanup frames
        self.cleanup_frames(frame_paths)
        
        if success:
            return VideoResult(
                success=True,
                video_path=str(output_path),
                duration=duration
            )
        else:
            return VideoResult(success=False, error="Failed to create video")


def main():
    """Test the video generator."""
    # This would require actual files to test
    print("Video Generator Agent - Ready")
    print("Use the main pipeline to generate videos")


if __name__ == "__main__":
    main()
