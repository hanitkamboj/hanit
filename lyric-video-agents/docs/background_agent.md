# Background Agent Documentation

## Overview
The **Background Agent** finds and downloads high-quality, watermark-free background images for lyric videos. It searches multiple free image sources and falls back to local assets.

## Location
`agents/background_agent/background_agent.py`

## Class: `BackgroundAgent`

### Configuration
Reads from `config.yaml`:
- `paths.background_dir` - Local background storage directory
- `background.min_resolution` - Minimum image resolution (default: 1920x1080)
- `background.no_watermark` - Require watermark-free images

### Dependencies
- `requests` - HTTP downloads
- `unsplash-python` - Unsplash API (optional)
- `pexels` - Pexels API (optional)

### Main Method: `process(meta=None, title=None, artist=None, genre=None, custom_query=None)`

**Parameters:**
- `meta` (SongMeta): Song metadata
- `title` (str): Song title
- `artist` (str): Artist name
- `genre` (str): Song genre
- `custom_query` (str): Override search query

**Returns:** `BackgroundResult` dataclass:
- `success` (bool)
- `image_path` (str): Path to downloaded background image
- `source` (str): Source name ("local", "unsplash", "pexels")
- `error` (str): Error message if failed

### Source Priority
1. **Local assets** - `assets/backgrounds/*.{jpg,jpeg,png,webp}` (random selection)
2. **Unsplash** - High-quality photos, requires API key
3. **Pexels** - Free stock photos, requires API key

### Keyword Generation
Generates search keywords from song metadata:
- **Title themes**: love→heart/romance, night→dark/stars/moon, dream→cloud/sky, sad→rain/alone, happy→sun/bright, fire→flame/burn, water→ocean/waves
- **Genre keywords**: pop→colorful/vibrant, rock→dark/edgy, electronic→neon/abstract, acoustic→nature/warm
- **Defaults**: aesthetic, abstract, colorful, artistic

### Image Filtering
- Minimum resolution: 1920x1080 (configurable)
- Landscape orientation preferred
- No watermarks (Unsplash/Pexels provide clean images)

### Usage Example
```python
from agents.background_agent import BackgroundAgent

agent = BackgroundAgent()
result = agent.process(
    title="Die With A Smile",
    artist="Lady Gaga Bruno Mars",
    genre="pop"
)
if result.success:
    print(f"Background: {result.image_path}")
    print(f"Source: {result.source}")
```

---

## Internal Methods

### `search_unsplash(query, count=5) -> List[dict]`
Unsplash API search with landscape orientation, high content filter.
Returns: `url`, `download_url`, `width`, `height`, `photographer`, `source`

### `search_pexels(query, count=5) -> List[dict]`
Pexels API search with large size, landscape orientation.
Returns: `url`, `download_url`, `width`, `height`, `photographer`, `source`

### `get_local_backgrounds() -> List[Path]`
Scans `assets/backgrounds/` for image files.

### `download_image(url, output_path) -> bool`
Streams download with 8KB chunks.

### `generate_keywords(meta, title, artist, genre) -> List[str]`
Creates search keywords from song metadata.

---

## Environment Variables
- `UNSPLASH_ACCESS_KEY` - Unsplash API key (from https://unsplash.com/developers)
- `PEXELS_API_KEY` - Pexels API key (from https://www.pexels.com/api/)

---

## Local Background Setup
Place images in `assets/backgrounds/`:
```bash
# Any JPG, PNG, or WebP files
cp my_background.jpg /workspaces/hanit/lyric-video-agents/assets/backgrounds/
```

The agent will randomly select from local images if available.

---

## Testing
```bash
cd /workspaces/hanit/lyric-video-agents
python3 -c "
from agents.background_agent import BackgroundAgent
agent = BackgroundAgent()
result = agent.process(title='Die With A Smile', artist='Lady Gaga', genre='pop')
print(f'Success: {result.success}, Source: {result.source}, Path: {result.image_path}')
"
```

---

## Integration Points
- **Called by**: Main pipeline after LRC Agent
- **Consumes**: SongMeta (title, artist, genre)
- **Feeds**: Video Generator (provides background_path)

---

## Customization
- Add new image sources (Google Images, Bing, etc.)
- Modify `generate_keywords()` for better thematic matching
- Add color palette extraction from album art
- Implement AI-based image generation (DALL-E, Stable Diffusion)
- Add blur/dim preview before download
- Cache downloaded images to avoid re-downloads