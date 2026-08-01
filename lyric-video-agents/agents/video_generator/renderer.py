"""
Video Renderer - Core rendering engine for smooth lyric videos.
Uses Pillow for image composition and moviepy for video encoding.
"""
import math
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from dataclasses import dataclass

from models import LyricLine, Word, FontSettings, AnimationSettings, VideoSettings
from utils import logger


@dataclass
class RenderFrame:
    """Data for a single rendered frame."""
    image: Image.Image
    timestamp: float


class VideoRenderer:
    """High-performance video renderer for lyric videos."""
    
    def __init__(self, font_settings: FontSettings, animation_settings: AnimationSettings,
                 video_settings: VideoSettings):
        self.font_settings = font_settings
        self.anim_settings = animation_settings
        self.video_settings = video_settings
        
        # Parse resolution
        self.width, self.height = map(int, video_settings.resolution.value.split('x'))
        
        # Load font
        try:
            self.font = ImageFont.truetype(font_settings.path, font_settings.size)
            self.font_small = ImageFont.truetype(font_settings.path, int(font_settings.size * 0.7))
        except Exception as e:
            logger.warning(f"Could not load font {font_settings.path}, using default: {e}")
            self.font = ImageFont.load_default()
            self.font_small = self.font
        
        # Pre-calculate layout
        self.line_height = int(font_settings.size * 1.4)
        self.visible_lines = self.height // self.line_height + 4  # Extra for smooth scrolling
        
    def create_background(self, bg_path: str) -> Image.Image:
        """Create blurred/dimmed background image."""
        # Load and resize background
        bg = Image.open(bg_path).convert('RGB')
        bg = bg.resize((self.width, self.height), Image.Resampling.LANCZOS)
        
        # Apply blur
        blur_radius = 20
        bg = bg.filter(ImageFilter.GaussianBlur(blur_radius))
        
        # Apply dim overlay
        dim_overlay = Image.new('RGB', (self.width, self.height), (0, 0, 0))
        dim_opacity = 0.3
        bg = Image.blend(bg, dim_overlay, dim_opacity)
        
        # Add vignette
        vignette = self._create_vignette()
        bg = Image.alpha_composite(bg.convert('RGBA'), vignette).convert('RGB')
        
        return bg
    
    def _create_vignette(self) -> Image.Image:
        """Create vignette overlay."""
        vignette = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(vignette)
        
        # Radial gradient from center
        center_x, center_y = self.width // 2, self.height // 2
        max_radius = math.sqrt(center_x**2 + center_y**2)
        
        for i in range(100):
            radius = int(max_radius * (i / 100))
            opacity = int(255 * (i / 100) * 0.55)
            draw.ellipse(
                [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
                outline=(0, 0, 0, opacity)
            )
        
        return vignette
    
    def render_frame(self, background: Image.Image, lines: List[LyricLine], 
                    current_time: float) -> Image.Image:
        """Render a single frame with lyrics at the given timestamp."""
        frame = background.copy()
        draw = ImageDraw.Draw(frame)
        
        # Find active line
        active_idx = self._find_active_line(lines, current_time)
        
        # Calculate scroll offset (smooth lerp)
        scroll_offset = self._calculate_scroll(lines, active_idx, current_time)
        
        # Render visible lines
        start_idx = max(0, active_idx - self.visible_lines // 2)
        end_idx = min(len(lines), active_idx + self.visible_lines // 2 + 1)
        
        for i in range(start_idx, end_idx):
            line = lines[i]
            
            # Calculate line position
            y_pos = self._calculate_line_y(i, active_idx, scroll_offset)
            
            # Skip if off-screen
            if y_pos < -self.line_height or y_pos > self.height + self.line_height:
                continue
            
            # Calculate line properties
            distance = abs(i - active_idx) if active_idx >= 0 else 99
            is_active = (i == active_idx)
            
            # Opacity and scale
            if is_active:
                opacity = 255
                scale = self.anim_settings.active_line_scale
            else:
                opacity = int(255 * self.anim_settings.inactive_opacity * 
                             max(0, 1 - distance * 0.15))
                scale = self.anim_settings.inactive_line_scale
            
            # Render line
            self._render_line(draw, line, y_pos, opacity, scale, current_time, is_active)
        
        return frame
    
    def _find_active_line(self, lines: List[LyricLine], current_time: float) -> int:
        """Find the currently active lyric line."""
        for i in range(len(lines) - 1, -1, -1):
            if current_time >= lines[i].start_time:
                return i
        return -1
    
    def _calculate_scroll(self, lines: List[LyricLine], active_idx: int, 
                         current_time: float) -> float:
        """Calculate smooth scroll offset."""
        if active_idx < 0:
            return 0.0
        
        # Target position: center the active line
        target_y = self.height * 0.38
        line_y = active_idx * self.line_height
        
        # Smooth interpolation
        scroll_speed = self.anim_settings.scroll_speed
        return target_y - line_y
    
    def _calculate_line_y(self, line_idx: int, active_idx: int, scroll_offset: float) -> float:
        """Calculate Y position for a line."""
        base_y = line_idx * self.line_height
        return base_y + scroll_offset
    
    def _render_line(self, draw: ImageDraw.Draw, line: LyricLine, y_pos: float,
                    opacity: int, scale: float, current_time: float, is_active: bool):
        """Render a single lyric line with word-level highlighting."""
        # Calculate text position (centered)
        text_bbox = draw.textbbox((0, 0), line.text, font=self.font)
        text_width = text_bbox[2] - text_bbox[0]
        x_start = (self.width - text_width) // 2
        
        # Apply shadow
        shadow_color = (*self._hex_to_rgb(self.font_settings.shadow_color), opacity)
        shadow_offset = self.font_settings.shadow_offset
        
        if is_active:
            # Render with word-level highlighting
            self._render_line_with_words(
                draw, line, x_start, y_pos, opacity, current_time
            )
        else:
            # Render simple line
            text_color = (*self._hex_to_rgb(self.font_settings.color), opacity)
            
            # Shadow
            draw.text(
                (x_start + shadow_offset, y_pos + shadow_offset),
                line.text,
                font=self.font,
                fill=shadow_color
            )
            
            # Main text
            draw.text(
                (x_start, y_pos),
                line.text,
                font=self.font,
                fill=text_color
            )
    
    def _render_line_with_words(self, draw: ImageDraw.Draw, line: LyricLine,
                               x_start: float, y_pos: float, opacity: int,
                               current_time: float):
        """Render line with word-by-word highlighting."""
        x_pos = x_start
        
        for word in line.words:
            # Calculate word progress
            if word.end_time > word.start_time:
                progress = (current_time - word.start_time) / (word.end_time - word.start_time)
                progress = max(0, min(1, progress))
            else:
                progress = 1.0 if current_time >= word.start_time else 0.0
            
            # Get word bbox
            word_bbox = draw.textbbox((0, 0), word.word, font=self.font)
            word_width = word_bbox[2] - word_bbox[0]
            
            # Determine color based on progress
            if progress >= 1.0:
                # Completed - highlight color
                color = self._hex_to_rgb(self.font_settings.highlight_color)
            elif progress > 0:
                # In progress - blend colors
                base_color = self._hex_to_rgb(self.font_settings.color)
                highlight_color = self._hex_to_rgb(self.font_settings.highlight_color)
                color = self._blend_colors(base_color, highlight_color, progress)
            else:
                # Not started - base color
                color = self._hex_to_rgb(self.font_settings.color)
            
            text_color = (*color, opacity)
            
            # Shadow
            shadow_color = (*self._hex_to_rgb(self.font_settings.shadow_color), opacity // 2)
            draw.text(
                (x_pos + self.font_settings.shadow_offset, 
                 y_pos + self.font_settings.shadow_offset),
                word.word,
                font=self.font,
                fill=shadow_color
            )
            
            # Main text
            draw.text((x_pos, y_pos), word.word, font=self.font, fill=text_color)
            
            # Move to next word position
            x_pos += word_width + draw.textbbox((0, 0), " ", font=self.font)[2]
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _blend_colors(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int],
                     progress: float) -> Tuple[int, int, int]:
        """Blend two colors based on progress."""
        return tuple(
            int(c1 + (c2 - c1) * progress)
            for c1, c2 in zip(color1, color2)
        )
