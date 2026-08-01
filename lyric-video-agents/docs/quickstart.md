# Quick Start Guide

## Prerequisites

### System Requirements
- **Python 3.10+** (tested on 3.12)
- **FFmpeg** (for video encoding)
- **4GB+ RAM** (for frame rendering)
- **2GB+ disk** (temp frames + output)

### Install System Dependencies
```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y ffmpeg

# macOS
brew install ffmpeg

# Windows (chocolatey)
choco install ffmpeg
```

### Python Dependencies
```bash
cd /workspaces/hanit/lyric-video-agents
pip install -r requirements.txt
```

## Setup

### 1. Clone/Navigate to Project
```bash
cd /workspaces/hanit/lyric-video-agents
```

### 2. Configure API Keys
```bash
cp .env.example .env
# Edit .env with your API keys
nano .env
```

**Required for full functionality:**
- `GENIUS_ACCESS_TOKEN` - Get from https://genius.com/api-clients
- `UNSPLASH_ACCESS_KEY` - Get from https://unsplash.com/developers
- `PEXELS_API_KEY` - Get from https://www.pexels.com/api/
- `SPOTIFY_CLIENT_ID` + `SPOTIFY_CLIENT_SECRET` - Get from https://developer.spotify.com/dashboard

**For YouTube upload:**
1. Go to https://console.cloud.google.com/
2. Enable YouTube Data API v3
3. Create OAuth 2.0 Client ID (Desktop app)
4. Download `client_secrets.json` to project root

### 3. Font Setup (Already done)
```bash
# edosz.ttf is in the repo, copied to assets/fonts/
ls assets/fonts/edosz.ttf
```

### 4. Background Images (Optional)
```bash
# Add your own backgrounds to assets/backgrounds/
cp your_image.jpg assets/backgrounds/
```

## Usage

### Basic Generation
```bash
# From song title + artist
python pipeline.py --title "Die With A Smile" --artist "Lady Gaga Bruno Mars"

# From search query
python pipeline.py --query "Lady Gaga Bruno Mars Die With A Smile"

# From Spotify URL
python pipeline.py --spotify-url "https://open.spotify.com/track/..."

# Auto-upload to YouTube (requires OAuth setup)
python pipeline.py --query "..." --upload
```

### Programmatic Usage
```python
from pipeline import LyricVideoPipeline

pipeline = LyricVideoPipeline()

# Generate video
result = pipeline.run(
    query="Die With A Smile Lady Gaga Bruno Mars"
)

if result.success:
    print(f"✅ Video: {result.video_path}")
    print(f"📝 Title: {result.seo_data.title}")
    print(f"🏷️ Tags: {len(result.seo_data.tags)}")
else:
    print(f"❌ Failed: {result.error}")
```

## Example Run

```bash
$ python pipeline.py --title "Die With A Smile" --artist "Lady Gaga Bruno Mars"

============================================================
                   🎬 LYRIC VIDEO PIPELINE                   
============================================================

2026-08-01 13:48:32 - STEP 1/5: Finding audio...

============================================================
                       🎵 AUDIO AGENT                        
============================================================

2026-08-01 13:48:32 - Searching YouTube for: Die With A Smile Lady Gaga Bruno Mars
2026-08-01 13:48:35 - ✓ Audio downloaded: assets/audio/Lady Gaga & Bruno Mars - Die With A Smile.m4a

2026-08-01 13:48:35 - STEP 2/5: Finding lyrics...

============================================================
                       📝 LRC AGENT                         
============================================================

2026-08-01 13:48:35 - Searching lyrics for: Die With A Smile by Lady Gaga Bruno Mars
2026-08-01 13:48:36 - Trying Hanit API...
2026-08-01 13:48:37 - ✓ Found 42 lyric lines from hanit_api

2026-08-01 13:48:37 - STEP 3/5: Finding background...

============================================================
                       🖼️  BACKGROUND AGENT                 
============================================================

2026-08-01 13:48:37 - Search keywords: romantic, pop, colorful, vibrant, love
2026-08-01 13:48:38 - ✓ Background downloaded: assets/backgrounds/bg_romantic_unsplash.jpg

2026-08-01 13:48:38 - STEP 4/5: Generating video...

============================================================
                     🎬 VIDEO GENERATOR AGENT               
============================================================

2026-08-01 13:48:38 - Audio duration: 215.42s
2026-08-01 13:48:38 - Generating 12925 frames at 60fps...
2026-08-01 13:55:12 - ✓ Generated 12925 frames
2026-08-01 13:55:12 - Creating video with moviepy...
2026-08-01 13:58:45 - ✓ Video created successfully: assets/output/Lady Gaga & Bruno Mars - Die With A Smile (Lyrics).mp4

2026-08-01 13:58:45 - STEP 5/5: Generating SEO metadata...

============================================================
                       🔍 SEO AGENT                         
============================================================

2026-08-01 13:58:45 - Generating title...
2026-08-01 13:58:45 - Generating timestamps...
2026-08-01 13:58:45 - Generating description...
2026-08-01 13:58:45 - Generating tags...
2026-08-01 13:58:45 - ✓ SEO metadata generated successfully

============================================================
✅ PIPELINE COMPLETED
🎬 Video: assets/output/Lady Gaga & Bruno Mars - Die With A Smile (Lyrics).mp4
🏷️ Title: Lady Gaga & Bruno Mars - Die With A Smile (Lyrics)
📄 SEO metadata saved alongside video
============================================================
```

## Output Files

After successful run:
```
assets/output/
├── Lady Gaga & Bruno Mars - Die With A Smile (Lyrics).mp4
├── Lady Gaga & Bruno Mars - Die With A Smile (Lyrics)_seo.json
└── Lady Gaga & Bruno Mars - Die With A Smile (Lyrics)_lyrics.json
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: moviepy.editor` | Use MoviePy 2.x imports (already fixed) |
| `FFmpeg not found` | Install ffmpeg: `sudo apt-get install ffmpeg` |
| `yt-dlp search failed` | Update yt-dlp: `pip install -U yt-dlp` |
| `Genius API 403` | Check `GENIUS_ACCESS_TOKEN` in .env |
| `No backgrounds found` | Add images to `assets/backgrounds/` or set API keys |
| `Font not found` | Ensure `assets/fonts/edosz.ttf` exists |
| `YouTube upload 403` | Check OAuth credentials, quota limits |
| `Out of memory` | Reduce resolution in config.yaml |

## Customization

### Change Video Quality
Edit `config.yaml`:
```yaml
video:
  resolution: "3840x2160"  # 4K
  fps: 60
  bitrate: "15000k"
```

### Change Font
```bash
# Replace font file
cp your_font.ttf assets/fonts/edosz.ttf
# Or update config.yaml font.path
```

### Change Animation Style
```yaml
animation:
  scroll_speed: 0.14      # Smoothness (0.1-0.3)
  inactive_opacity: 0.4   # Dim non-active lines
  blur_amount: 6          # Blur radius for inactive
```

## Next Steps

1. **Add API keys** to .env for full functionality
2. **Test with a real song** using `--query`
3. **Set up YouTube OAuth** for auto-upload
4. **Customize branding** in SEO agent (social links, disclaimer)
5. **Add local backgrounds** for consistent style

## Support

- Check `docs/` for detailed agent documentation
- Logs show step-by-step progress
- Each agent can be tested independently