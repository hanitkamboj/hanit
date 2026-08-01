# Lyric Video Generator - Multi-Agent Pipeline

A complete, production-ready system for generating high-quality lyric videos (1080p/4K 60fps) with automated YouTube upload, following TheCloudLyric channel style.

## Features

- 🎵 **Audio Agent** - Downloads high-quality audio from YouTube/Spotify
- 📝 **LRC Agent** - Finds synced lyrics (word-level timing) from multiple sources
- 🖼️ **Background Agent** - Downloads watermark-free backgrounds from Unsplash/Pexels
- 🎬 **Video Generator** - Smooth 60fps rendering with word-by-word highlighting
- 🔍 **SEO Agent** - Generates optimized titles, descriptions, tags, hashtags, timestamps
- 📺 **YouTube Uploader** - Automated upload with metadata and thumbnails

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt
sudo apt-get install ffmpeg  # or brew install ffmpeg

# Configure API keys
cp .env.example .env
# Edit .env with your keys

# Generate a lyric video
python pipeline.py --title "Die With A Smile" --artist "Lady Gaga Bruno Mars"

# With auto-upload to YouTube
python pipeline.py --query "Song Name" --upload
```

## Documentation

| Document | Description |
|----------|-------------|
| [Quick Start](docs/quickstart.md) | Installation and first run |
| [Pipeline Overview](docs/pipeline.md) | Architecture and data flow |
| [Audio Agent](docs/audio_agent.md) | Audio downloading & metadata |
| [LRC Agent](docs/lrc_agent.md) | Lyrics fetching & parsing |
| [Background Agent](docs/background_agent.md) | Background image sourcing |
| [Video Generator](docs/video_generator.md) | Rendering engine details |
| [SEO Agent](docs/seo_agent.md) | YouTube metadata generation |
| [YouTube Uploader](docs/youtube_uploader.md) | Upload automation |

## Configuration

All settings in `config.yaml`:
- Video: resolution, fps, codec, bitrate
- Font: family, size, colors, shadows
- Animation: scroll speed, opacity, blur
- Agents: enabled/disabled, sources, quality

## Requirements

- Python 3.10+
- FFmpeg
- API keys (optional but recommended):
  - Genius (lyrics)
  - Unsplash/Pexels (backgrounds)
  - Spotify (metadata)
  - YouTube OAuth (upload)

## Output

```
assets/output/
├── Artist - Title (Lyrics).mp4          # Final video
├── Artist - Title (Lyrics)_seo.json     # SEO metadata
└── Artist - Title (Lyrics)_lyrics.json  # Lyrics for reuse
```

## Example Output

**Video Specs:**
- 1920×1080 or 3840×2160 @ 60fps
- H.264 / AAC, 8000+ kbps
- Word-level karaoke highlighting
- Smooth scrolling (Apple Music style)

**SEO Format (TheCloudLyric style):**
```
Lady Gaga & Bruno Mars - Die With A Smile (Lyrics)

🎵 Enjoy the lyric video for "Die With A Smile"...
Full lyrics on screen throughout...

🎧 Song: Die With A Smile
🎤 Artists: Lady Gaga, Bruno Mars
📅 Released: August 16, 2024
💿 Album: Mayhem (2025)

LYRICS:
[Full formatted lyrics]

⏱️ TIMESTAMPS
00:00 Intro
00:29 Verse 1
...

👍 Like & Subscribe!
#LadyGaga #BrunoMars #DieWithASmile
```

## Architecture

```
Input → Audio Agent → LRC Agent → Background Agent → Video Generator → SEO Agent → YouTube Uploader
            │            │              │                   │              │
            ▼            ▼              ▼                   ▼              ▼
         .m4a audio  LyricLine[]    bg_image.jpg       video.mp4       YouTube URL
         SongMeta   (word timing)   (1920x1080+)      (60fps smooth)  + metadata
```

## Customization

- **Fonts**: Replace `assets/fonts/edosz.ttf`
- **Colors**: Edit `config.yaml` font colors
- **Animation**: Adjust scroll_speed, blur, opacity
- **SEO Template**: Modify `agents/seo_agent/seo_agent.py`
- **Add Agents**: Follow pattern in `agents/`

## License

MIT - See LICENSE file

## Contributing

1. Fork the repo
2. Create feature branch
3. Add tests for new agents
4. Update documentation
5. Submit PR