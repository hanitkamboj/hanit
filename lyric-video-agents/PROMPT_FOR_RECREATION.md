# Prompt: Build a Multi-Agent Lyric Video Generation Pipeline

## System Overview
Create a complete, production-ready Python system that generates high-quality lyric videos (1080p/4K @ 60fps) with automated YouTube upload, following the style of TheCloudLyric YouTube channel.

## Core Requirements

### Video Output Specifications
- **Resolution**: 1920x1080 (HD) or 3840x2160 (4K) — configurable
- **Frame Rate**: 60 fps (smooth motion)
- **Codec**: H.264 (libx264) / AAC audio
- **Bitrate**: 8000k+ (high quality)
- **Font**: 60px centered, custom TTF (edosz.ttf provided)
- **Animation**: Word-by-word karaoke highlighting, smooth scrolling (lerp 0.14), inactive lines dimmed/blurred

### Agent Architecture (6 Agents)

```
Input → Audio Agent → LRC Agent → Background Agent → Video Generator → SEO Agent → YouTube Uploader
```

---

## Agent 1: Audio Agent
**Purpose**: Find & download high-quality audio
- **Sources**: YouTube (via yt-dlp), Spotify metadata (via Hanit API)
- **Output**: `.m4a` file + `SongMeta` (title, artist, album, duration, cover_url, spotify_url)
- **Quality**: Best available (m4a, 256kbps+)
- **Deduplication**: Skip if file exists

---

## Agent 2: LRC Agent
**Purpose**: Find & parse synchronized lyrics with word-level timing
- **Sources** (priority order):
  1. Hanit API (Spotify synced lyrics): `GET {base}/getLyrics?url={spotify_url}`
  2. LRCLib direct: `https://lrclib.net/api/get?track_name={title}&artist_name={artist}&duration={ms}`
  3. LRCLib search: `https://lrclib.net/api/search?q={query}`
  4. Genius.com (plain text → estimated timing)
- **Output**: `List[LyricLine]` with `Word` objects (start_time, end_time per word)
- **Fallback**: Convert plain lyrics to timed format (~0.5s per word)

---

## Agent 3: Background Agent
**Purpose**: Download watermark-free, relevant background images
- **Sources**: Local (`assets/backgrounds/`), Unsplash API, Pexels API
- **Minimum**: 1920x1080, landscape
- **Keyword generation**: From song title/genre (love→romance, night→dark/stars, pop→colorful, etc.)
- **No watermarks**: Unsplash/Pexels provide clean images

---

## Agent 4: Video Generator
**Purpose**: Render smooth 60fps lyric video
- **Renderer**: Pillow (frame generation) + MoviePy 2.x (encoding)
- **Background processing**: Blur(20) + dim(30%) + vignette(55%) + film grain
- **Animation** (matching workspace zip logic):
  - Active line: 100% opacity, scale 1.0, centered at 38% screen height
  - Inactive: 40% opacity, scale 0.97, blur up to 6px (distance-based)
  - Word highlight: Base white → Gold (#FFD700) interpolation per frame
  - Smooth scroll: lerp factor 0.14
- **Output**: MP4 at target resolution/fps

---

## Agent 5: SEO Agent
**Purpose**: Generate TheCloudLyric-format YouTube metadata
- **Title**: `{Artist} - {Title} (Lyrics)`
- **Description**: Full template with song info, lyrics, timestamps, CTA, social links, disclaimer
- **Tags**: 30 optimized tags (artist, title, album, genre, variations, discovery)
- **Hashtags**: 15 max (`#ArtistName #SongTitle #Genre #Lyrics #LyricVideo`)
- **Timestamps**: Auto-detect sections (Intro, Verse, Chorus, Bridge, Outro) from lyric text

---

## Agent 6: YouTube Uploader
**Purpose**: Automated upload via YouTube Data API v3
- **Auth**: OAuth 2.0 (Desktop app), token cached in `token.json`
- **Metadata**: Title, description, tags, category (10=Music), privacy status
- **Thumbnail**: Optional custom upload
- **Resumable**: 10MB chunks with progress logging

---

## Configuration (config.yaml)
All settings externalized:
- Video: resolution, fps, codec, bitrate, preset
- Font: path, size, colors, shadow
- Animation: scroll_speed, opacity, blur, scales
- Background: style, blur_radius, dim_opacity
- API endpoints (Hanit API)
- YouTube: category, privacy, auto_upload
- Paths: audio_dir, background_dir, output_dir, temp_dir
- Agent enable/disable flags

## Data Models (models.py)
```python
SongMeta: title, artist, album, release_date, genre, label, duration, spotify_url, cover_url
LyricLine: id, text, start_time, end_time, words[], translation, roman, is_duet, is_background
Word: word, start_time, end_time
SEOData: title, description, tags[], hashtags[], timestamps{}, thumbnail_path
Result dataclasses for each agent (success, data..., error)
```

## Pipeline Orchestrator (pipeline.py)
- CLI: `--query`, `--spotify-url`, `--title --artist`, `--upload`
- Programmatic: `LyricVideoPipeline().run()`
- Sequential execution with early exit on failure
- Saves SEO JSON + lyrics JSON alongside video

## Documentation Required
Create `.md` files for:
1. `quickstart.md` - Install & first run
2. `pipeline.md` - Architecture & data flow
3. `config.md` - Full config reference
4. `audio_agent.md`, `lrc_agent.md`, `background_agent.md`, `video_generator.md`, `seo_agent.md`, `youtube_uploader.md` - Per-agent deep docs

## Dependencies
```
moviepy>=2.0.0, Pillow, numpy, yt-dlp, requests, beautifulsoup4, lxml
google-api-python-client, google-auth-oauthlib, google-auth-httplib2
python-dotenv, pyyaml, tqdm, colorama
```
System: ffmpeg

## Environment Variables (.env)
```
GENIUS_ACCESS_TOKEN, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
UNSPLASH_ACCESS_KEY, PEXELS_API_KEY
# client_secrets.json in project root (not in .env)
```

## Deliverables
- Complete runnable Python project
- All 6 agents with typed interfaces
- Configuration system
- CLI + programmatic entry points
- 10+ markdown documentation files
- README.md with quick start
- Requirements.txt

## Quality Standards
- Type hints throughout
- Error handling with Result dataclasses
- Logging with timestamps
- Progress bars for long operations
- Temp file cleanup
- No hardcoded secrets
- Modular, extensible agent pattern