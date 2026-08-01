# Pipeline Overview

## Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                    LYRIC VIDEO PIPELINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐   ┌──────────┐   ┌────────────┐   ┌───────────┐  │
│  │  AUDIO   │──▶│   LRC    │──▶│ BACKGROUND │──▶│  VIDEO    │  │
│  │  AGENT   │   │  AGENT   │   │  AGENT     │   │ GENERATOR │  │
│  └──────────┘   └──────────┘   └────────────┘   └───────────┘  │
│       │             │                │                 │         │
│       ▼             ▼                ▼                 ▼         │
│  .m4a audio   LyricLine[]       bg_image.jpg      video.mp4     │
│  SongMeta                              duration          SEOData │
│                                                                  │
│                                              ┌─────────────┐    │
│                                              │    SEO      │    │
│                                              │   AGENT     │    │
│                                              └─────────────┘    │
│                                                     │            │
│                                                     ▼            │
│                                              ┌─────────────┐    │
│                                              │  YOUTUBE    │    │
│                                              │  UPLOADER   │    │
│                                              └─────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

| Stage | Input | Output |
|-------|-------|--------|
| 1. Audio | query / spotify_url | `audio_path`, `SongMeta` |
| 2. LRC | SongMeta, title/artist | `List[LyricLine]`, `lrc_text` |
| 3. Background | SongMeta, genre | `background_path` |
| 4. Video | audio, lyrics, background | `video_path`, `duration` |
| 5. SEO | SongMeta, lyrics | `SEOData` (title, desc, tags, hashtags, timestamps) |
| 6. Upload | video, SEOData | YouTube `video_id`, `video_url` |

## Entry Points

### CLI (pipeline.py)
```bash
# Search by query
python pipeline.py --query "Lady Gaga Die With A Smile"

# From Spotify URL
python pipeline.py --spotify-url "https://open.spotify.com/track/..."

# From title + artist
python pipeline.py --title "Die With A Smile" --artist "Lady Gaga Bruno Mars"

# Auto-upload to YouTube
python pipeline.py --query "..." --upload
```

### Programmatic
```python
from pipeline import LyricVideoPipeline

pipeline = LyricVideoPipeline()
result = pipeline.run(
    query="Die With A Smile Lady Gaga Bruno Mars",
    auto_upload=False
)

if result.success:
    print(f"Video: {result.video_path}")
    print(f"SEO Title: {result.seo_data.title}")
```

## Configuration

All settings in `config.yaml`:

```yaml
video:
  resolution: "1920x1080"    # or "3840x2160"
  fps: 60
  codec: "libx264"
  bitrate: "8000k"
  preset: "slow"

font:
  family: "edosz"
  path: "assets/fonts/edosz.ttf"
  size: 60
  color: "#FFFFFF"
  highlight_color: "#FFD700"

animation:
  scroll_speed: 0.14
  inactive_opacity: 0.4
  blur_amount: 6

agents:
  audio_agent:
    enabled: true
    quality: "best"
  lrc_agent:
    enabled: true
    sources: ["hanit_api", "lrclib", "genius"]
  background_agent:
    enabled: true
    min_resolution: "1920x1080"
    no_watermark: true
  youtube_uploader:
    enabled: false
    auto_upload: false
```

## Required API Keys (in .env)
```bash
GENIUS_ACCESS_TOKEN=        # Genius lyrics
SPOTIFY_CLIENT_ID=          # Spotify metadata
SPOTIFY_CLIENT_SECRET=
UNSPLASH_ACCESS_KEY=        # Background images
PEXELS_API_KEY=
# YouTube: place client_secrets.json in root
```

## Output Structure
```
assets/
├── audio/           # Downloaded .m4a files
├── backgrounds/     # Local/custom backgrounds
├── fonts/           # edosz.ttf
└── output/          # Generated videos + SEO JSON
    ├── Artist - Title (Lyrics).mp4
    ├── Artist - Title (Lyrics)_seo.json
    └── Artist - Title (Lyrics)_lyrics.json
```

## Performance
- **Frame rendering**: ~1-3s per frame (CPU)
- **1080p 60fps 3min song**: ~10,800 frames → 3-9 hours CPU
- **MoviePy encoding**: ~2-5x realtime
- **Total**: ~30-60 min for 3-min song (single-threaded)

## Optimization Tips
1. **Reduce resolution**: 1280x720 for faster renders
2. **Lower FPS**: 30fps halves frame count
3. **Parallel frames**: Use multiprocessing.Pool (TODO)
4. **Hardware encoding**: NVENC/QSV via ffmpeg flags
5. **Cache backgrounds**: Reuse for same artist/genre

## Error Handling
Each agent returns `*Result` dataclass with:
- `success: bool`
- `error: str` (if failed)
- Data fields (if succeeded)

Pipeline stops on first failure and returns error.

## Extending the Pipeline
Add new agents by:
1. Create `agents/new_agent/new_agent.py` with `NewAgent` class
2. Add `process()` method returning `NewResult`
3. Register in `agents/__init__.py`
4. Add step in `LyricVideoPipeline.run()`
5. Document in `docs/new_agent.md`

## Monitoring
- Logs: Console output with timestamps
- Progress: tqdm bars for frame generation + upload
- Temp files: `/tmp/lyric-video-gen/` (auto-cleaned)