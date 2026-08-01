"""
Shared data models for all agents.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum


class Resolution(Enum):
    HD = "1920x1080"
    UHD = "3840x2160"


class BackgroundStyle(Enum):
    IMAGE = "image"
    GRADIENT = "gradient"
    BLUR = "blur"


class HighlightStyle(Enum):
    FILL = "fill"
    FADE = "fade"
    GLOW = "glow"


@dataclass
class Word:
    word: str
    start_time: float  # in seconds
    end_time: float    # in seconds


@dataclass
class LyricLine:
    id: int
    text: str
    start_time: float  # in seconds
    end_time: Optional[float] = None
    words: List[Word] = field(default_factory=list)
    translation: Optional[str] = None
    roman: Optional[str] = None
    is_duet: bool = False
    is_background: bool = False


@dataclass
class SongMeta:
    title: str
    artist: str
    album: Optional[str] = None
    release_date: Optional[str] = None
    genre: Optional[str] = None
    label: Optional[str] = None
    duration: Optional[float] = None  # in seconds
    spotify_url: Optional[str] = None
    cover_url: Optional[str] = None


@dataclass
class SongData:
    meta: SongMeta
    lyrics: List[LyricLine]
    audio_path: Optional[str] = None
    background_path: Optional[str] = None
    lrc_path: Optional[str] = None


@dataclass
class VideoSettings:
    resolution: Resolution = Resolution.HD
    fps: int = 60
    codec: str = "libx264"
    audio_codec: str = "aac"
    bitrate: str = "8000k"
    preset: str = "slow"


@dataclass
class FontSettings:
    family: str = "edosz"
    path: str = "assets/fonts/edosz.ttf"
    size: int = 60
    color: str = "#FFFFFF"
    highlight_color: str = "#FFD700"
    shadow_color: str = "#000000"
    shadow_offset: int = 2
    shadow_blur: int = 4


@dataclass
class AnimationSettings:
    scroll_speed: float = 0.14
    word_highlight_style: HighlightStyle = HighlightStyle.FILL
    active_line_scale: float = 1.0
    inactive_line_scale: float = 0.97
    inactive_opacity: float = 0.4
    blur_amount: float = 6.0
    transition_duration: float = 0.5


@dataclass
class SEOData:
    title: str
    description: str
    tags: List[str]
    hashtags: List[str]
    timestamps: Dict[str, str] = field(default_factory=dict)
    thumbnail_path: Optional[str] = None


@dataclass
class PipelineResult:
    success: bool
    video_path: Optional[str] = None
    seo_data: Optional[SEOData] = None
    error: Optional[str] = None
    song_data: Optional[SongData] = None
