# Agents Overview

This directory contains all the specialized agents that make up the lyric video generation pipeline.

## Agent List

| Agent | File | Purpose |
|-------|------|---------|
| **Audio Agent** | `audio_agent/audio_agent.py` | Find & download audio from YouTube/Spotify |
| **LRC Agent** | `lrc_agent/lrc_agent.py` | Find & parse synchronized lyrics |
| **Background Agent** | `background_agent/background_agent.py` | Find & download background images |
| **Video Generator** | `video_generator/video_generator.py` | Render smooth lyric videos |
| **SEO Agent** | `seo_agent/seo_agent.py` | Generate YouTube metadata |
| **YouTube Uploader** | `youtube_uploader/youtube_uploader.py` | Upload videos to YouTube |

## Common Interface

All agents follow the same pattern:

```python
class AgentName:
    def __init__(self, config: dict = None):
        # Initialize with config
        pass
    
    def process(self, **kwargs) -> ResultDataclass:
        # Main processing method
        # Returns Result with success/error/data
        pass
```

## Result Dataclasses

Each agent returns a typed result:

```python
@dataclass
class AudioResult:
    success: bool
    audio_path: str|None
    meta: SongMeta|None
    error: str|None

@dataclass
class LRCResult:
    success: bool
    lyrics: List[LyricLine]|None
    lrc_text: str|None
    source: str|None
    error: str|None

@dataclass
class BackgroundResult:
    success: bool
    image_path: str|None
    source: str|None
    error: str|None

@dataclass
class VideoResult:
    success: bool
    video_path: str|None
    duration: float|None
    error: str|None

@dataclass
class SEOResult:
    success: bool
    seo_data: SEOData|None
    error: str|None

@dataclass
class UploadResult:
    success: bool
    video_id: str|None
    video_url: str|None
    error: str|None
```

## Data Models (models.py)

Core data structures shared across agents:

```python
@dataclass
class SongMeta:
    title: str
    artist: str
    album: str|None
    release_date: str|None
    genre: str|None
    label: str|None
    duration: float|None
    spotify_url: str|None
    cover_url: str|None

@dataclass
class LyricLine:
    id: int
    text: str
    start_time: float
    end_time: float|None
    words: List[Word]
    translation: str|None
    roman: str|None
    is_duet: bool
    is_background: bool

@dataclass
class Word:
    word: str
    start_time: float
    end_time: float

@dataclass
class SEOData:
    title: str
    description: str
    tags: List[str]
    hashtags: List[str]
    timestamps: Dict[str, str]
    thumbnail_path: str|None
```

## Agent Communication Flow

```
Audio Agent
    │
    ├─▶ audio_path (str)
    └─▶ SongMeta ──▶ LRC Agent
                       │
                       ├─▶ List[LyricLine]
                       └─▶ lrc_text (str)
                              │
                              ▼
                    Background Agent
                              │
                              ├─▶ background_path (str)
                              ▼
                       Video Generator
                              │
                              ├─▶ video_path (str)
                              └─▶ duration (float)
                                     │
                                     ▼
                              SEO Agent
                                     │
                                     ├─▶ SEOData (title, desc, tags, hashtags, timestamps)
                                     ▼
                              YouTube Uploader
                                     │
                                     └─▶ video_id, video_url
```

## Adding a New Agent

1. Create directory: `agents/new_agent/`
2. Create `new_agent.py` with `NewAgent` class and `NewResult` dataclass
3. Create `__init__.py` exporting the class
4. Add import to `agents/__init__.py`
5. Add step in `pipeline.py` `LyricVideoPipeline.run()`
6. Document in `docs/new_agent.md`

## Testing Agents Individually

```bash
# Audio Agent
python -c "from agents.audio_agent import AudioAgent; a=AudioAgent(); r=a.process(query='song name'); print(r)"

# LRC Agent
python -c "from agents.lrc_agent import LRCAgent; a=LRCAgent(); r=a.process(title='Song', artist='Artist'); print(r)"

# Background Agent
python -c "from agents.background_agent import BackgroundAgent; a=BackgroundAgent(); r=a.process(title='Song', artist='Artist'); print(r)"

# Video Generator (needs real files)
python -c "from agents.video_generator import VideoGeneratorAgent; a=VideoGeneratorAgent(); print('Ready')"

# SEO Agent
python -c "from agents.seo_agent import SEOAgent; from models import SongMeta, LyricLine; a=SEOAgent(); m=SongMeta(title='T', artist='A'); l=[LyricLine(id=0, text='lyrics', start_time=0, words=[])]; r=a.process(m, l); print(r)"

# YouTube Uploader (needs auth)
python -c "from agents.youtube_uploader import YouTubeUploaderAgent; a=YouTubeUploaderAgent(); print('Ready')"
```