# Configuration Reference

## config.yaml

Complete configuration file with all options.

```yaml
# Lyric Video Generator Configuration
version: "1.0.0"

# ============================================================
# VIDEO SETTINGS
# ============================================================
video:
  resolution: "1920x1080"     # "1920x1080" (HD) or "3840x2160" (4K)
  fps: 60                     # Frame rate (60 for smooth motion)
  codec: "libx264"            # Video codec (H.264)
  audio_codec: "aac"          # Audio codec
  bitrate: "8000k"            # Video bitrate (quality)
  preset: "slow"              # Encoding preset: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
  pixel_format: "yuv420p"     # Pixel format for compatibility

# ============================================================
# FONT SETTINGS
# ============================================================
font:
  family: "edosz"             # Font family name
  path: "assets/fonts/edosz.ttf"  # Path to .ttf file
  size: 60                    # Font size in pixels (60px as requested)
  color: "#FFFFFF"            # Base text color (white)
  highlight_color: "#FFD700"  # Active word color (gold)
  shadow_color: "#000000"     # Text shadow color (black)
  shadow_offset: 2            # Shadow offset in pixels
  shadow_blur: 4              # Shadow blur radius

# ============================================================
# ANIMATION SETTINGS
# ============================================================
animation:
  scroll_speed: 0.14          # Lerp factor for smooth scrolling (0.1-0.3)
  word_highlight_style: "fill" # fill, fade, or glow
  active_line_scale: 1.0      # Scale for active line
  inactive_line_scale: 0.97   # Scale for inactive lines
  inactive_opacity: 0.4       # Opacity for inactive lines (0.0-1.0)
  blur_amount: 6              # Max blur for inactive lines (pixels)
  transition_duration: 0.5    # Transition duration (seconds)

# ============================================================
# BACKGROUND SETTINGS
# ============================================================
background:
  default_style: "image"      # image, gradient, or blur
  blur_radius: 20             # Background blur radius
  dim_opacity: 0.3            # Dim overlay opacity (0.0-1.0)
  vignette_strength: 0.55     # Vignette strength (0.0-1.0)

# ============================================================
# API SETTINGS (Use .env for secrets)
# ============================================================
api:
  genius_token: ""            # Set via GENIUS_ACCESS_TOKEN env
  spotify_client_id: ""       # Set via SPOTIFY_CLIENT_ID env
  spotify_client_secret: ""   # Set via SPOTIFY_CLIENT_SECRET env
  unsplash_access_key: ""     # Set via UNSPLASH_ACCESS_KEY env
  pexels_api_key: ""          # Set via PEXELS_API_KEY env
  youtube_client_secrets: "client_secrets.json"

# Hanit API (for Spotify lyrics)
hanit_api:
  base_url: "https://hanit-api.vercel.app/api/v1"
  get_song_data: "/getSongData"
  get_lyrics: "/getLyrics"

# ============================================================
# YOUTUBE SETTINGS
# ============================================================
youtube:
  category: "10"              # YouTube category ID (10 = Music)
  privacy_status: "public"    # public, private, or unlisted
  auto_upload: false          # Enable auto-upload in pipeline
  auto_generate_thumbnail: true

# ============================================================
# PATHS
# ============================================================
paths:
  audio_dir: "assets/audio"
  background_dir: "assets/backgrounds"
  output_dir: "assets/output"
  temp_dir: "/tmp/lyric-video-gen"

# ============================================================
# AGENT SETTINGS
# ============================================================
agents:
  audio_agent:
    enabled: true
    sources: ["youtube", "spotify"]
    quality: "best"           # best, high, medium

  lrc_agent:
    enabled: true
    sources: ["hanit_api", "lrclib", "genius"]
    fallback_to_sync: true    # Convert plain lyrics to timed if needed

  background_agent:
    enabled: true
    sources: ["unsplash", "pexels", "local"]
    min_resolution: "1920x1080"
    no_watermark: true

  seo_agent:
    enabled: true
    generate_timestamps: true
    optimize_tags: true

  youtube_uploader:
    enabled: false
    auto_upload: false
```

## Environment Variables (.env)

```bash
# ============================================================
# REQUIRED FOR FULL FUNCTIONALITY
# ============================================================

# Genius API - Lyrics scraping
# Get from: https://genius.com/api-clients
GENIUS_ACCESS_TOKEN=your_token_here

# Spotify API - Metadata & lyrics
# Get from: https://developer.spotify.com/dashboard
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret

# Unsplash API - High-quality backgrounds
# Get from: https://unsplash.com/developers
UNSPLASH_ACCESS_KEY=your_access_key

# Pexels API - Free stock photos
# Get from: https://www.pexels.com/api/
PEXELS_API_KEY=your_api_key

# YouTube OAuth - Auto-upload
# Download client_secrets.json from Google Cloud Console
# Place in project root (not in .env)

# ============================================================
# OPTIONAL
# ============================================================

# Google Custom Search - Alternative background search
GOOGLE_API_KEY=your_key
GOOGLE_CX=your_search_engine_id
```

## YouTube Category IDs

Common categories for music:
| ID | Category |
|----|----------|
| 10 | Music |
| 24 | Entertainment |
| 1 | Film & Animation |

Full list: https://developers.google.com/youtube/v3/docs/videoCategories/list

## Video Presets (Quality vs Speed)

| Preset | Speed | Quality | Use Case |
|--------|-------|---------|----------|
| ultrafast | Fastest | Lowest | Testing |
| veryfast | Very Fast | Low | Quick preview |
| fast | Fast | Medium | Development |
| medium | Medium | Good | Default |
| slow | Slow | Better | Production |
| slower | Very Slow | Best | Archival |
| veryslow | Slowest | Maximum | Final master |

**Recommendation**: Use `slow` or `slower` for final uploads.

## Resolution Options

| Resolution | Pixels | Aspect | Use Case |
|------------|--------|--------|----------|
| 1920x1080 | 2.1M | 16:9 | Standard HD (YouTube default) |
| 3840x2160 | 8.3M | 16:9 | 4K UHD (future-proof) |
| 2560x1440 | 3.7M | 16:9 | 2K QHD (middle ground) |

## Font Requirements

- Format: `.ttf` (TrueType)
- Recommended: Clean, readable sans-serif
- Size: 60px base (scales with resolution)
- The `edosz.ttf` font is included in the repo

## Animation Tuning Guide

| Parameter | Effect | Range | Default |
|-----------|--------|-------|---------|
| scroll_speed | Scroll smoothness | 0.05-0.3 | 0.14 |
| inactive_opacity | Dim inactive lines | 0.1-0.6 | 0.4 |
| blur_amount | Blur radius (px) | 2-12 | 6 |
| inactive_line_scale | Size reduction | 0.9-0.99 | 0.97 |

**For more "pop"**: Increase scroll_speed, decrease inactive_opacity
**For subtler**: Decrease scroll_speed, increase inactive_opacity

## Directory Structure

```
lyric-video-agents/
├── agents/
│   ├── audio_agent/
│   ├── lrc_agent/
│   ├── background_agent/
│   ├── video_generator/
│   ├── seo_agent/
│   └── youtube_uploader/
├── assets/
│   ├── audio/           # Downloaded audio
│   ├── backgrounds/     # Local backgrounds
│   ├── fonts/           # edosz.ttf
│   └── output/          # Generated videos + JSON
├── docs/                # Documentation
├── config.yaml          # Main configuration
├── .env.example         # Env template
├── pipeline.py          # Main entry point
├── models.py            # Data classes
└── utils.py             # Shared utilities
```

## Performance Tuning

### For Faster Generation
```yaml
video:
  resolution: "1280x720"
  fps: 30
  preset: "fast"
```

### For Maximum Quality
```yaml
video:
  resolution: "3840x2160"
  fps: 60
  preset: "veryslow"
  bitrate: "20000k"
```

### Memory Optimization
- Frames stored in `/tmp/lyric-video-gen/frames/`
- Auto-cleaned after encoding
- Ensure `/tmp` has sufficient space (4K 3min ≈ 2-4GB frames)