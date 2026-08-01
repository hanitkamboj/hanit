# Audio Agent Documentation

## Overview
The **Audio Agent** is responsible for finding and downloading high-quality audio files for lyric video generation. It searches YouTube using `yt-dlp` and can extract metadata from Spotify URLs via the Hanit API.

## Location
`agents/audio_agent/audio_agent.py`

## Class: `AudioAgent`

### Configuration
Reads from `config.yaml`:
- `paths.audio_dir` - Output directory for audio files
- `hanit_api.base_url` / `hanit_api.get_song_data` - Hanit API endpoints

### Dependencies
- `yt-dlp` - YouTube audio extraction
- `requests` - HTTP calls to Hanit API
- `ffmpeg` - Required by yt-dlp for audio conversion

### Main Method: `process(query=None, spotify_url=None, youtube_url=None)`

**Parameters:**
- `query` (str): Search query (e.g., "Lady Gaga Die With A Smile")
- `spotify_url` (str): Spotify track URL for metadata + search
- `youtube_url` (str): Direct YouTube URL to download

**Returns:** `AudioResult` dataclass:
- `success` (bool)
- `audio_path` (str): Path to downloaded .m4a file
- `meta` (SongMeta): Title, artist, album, duration, cover_url, spotify_url
- `error` (str): Error message if failed

### Workflow
1. **If Spotify URL provided**: Fetch metadata from Hanit API
2. **If query provided**: Search YouTube via `yt-dlp ytsearch1:`
3. **If YouTube URL provided**: Use directly
4. **Extract metadata** from YouTube if not already available
5. **Download audio** as M4A (best quality) using `yt-dlp --extract-audio --audio-format m4a --audio-quality 0`
6. **Return** audio file path and metadata

### Audio Quality Settings
```python
quality_map = {
    "best": "bestaudio[ext=m4a]/bestaudio",
    "high": "bestaudio[ext=m4a]/bestaudio", 
    "medium": "bestaudio[ext=m4a]/bestaudio"
}
```

### Error Handling
- Returns `AudioResult(success=False, error=...)` on any failure
- Handles: network errors, missing files, yt-dlp failures, timeouts
- Skips download if file already exists

### Usage Example
```python
from agents.audio_agent import AudioAgent

agent = AudioAgent()
result = agent.process(query="Die With A Smile Lady Gaga Bruno Mars")
if result.success:
    print(f"Audio: {result.audio_path}")
    print(f"Title: {result.meta.title}")
    print(f"Artist: {result.meta.artist}")
```

---

## Internal Methods

### `search_youtube(query) -> str|None`
Searches YouTube and returns the first result URL.

### `get_spotify_metadata(spotify_url) -> dict|None`
Calls Hanit API: `GET {base_url}/getSongData?url={spotify_url}`

### `download_audio(url, output_path, quality) -> bool`
Runs yt-dlp subprocess with audio extraction.

### `extract_metadata_from_ytdlp(url) -> dict|None`
Runs `yt-dlp --dump-json --no-download` to get video metadata.

---

## Environment Variables
None required (uses config.yaml paths)

---

## Testing
```bash
cd /workspaces/hanit/lyric-video-agents
python3 -c "
from agents.audio_agent import AudioAgent
agent = AudioAgent()
result = agent.process(query='Die With A Smile Lady Gaga Bruno Mars')
print(result)
"
```

---

## Integration Points
- **Called by**: Main pipeline (`pipeline.py`)
- **Feeds**: LRC Agent (provides SongMeta), Video Generator (provides audio_path)
- **Output**: .m4a audio file in `assets/audio/`

---

## Customization
- Change `audio_dir` in config.yaml to store audio elsewhere
- Add more sources (SoundCloud, Bandcamp) by extending `search_youtube`
- Modify quality settings in `download_audio`
- Add caching layer for repeated searches