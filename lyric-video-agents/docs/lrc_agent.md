# LRC Agent Documentation

## Overview
The **LRC Agent** finds and parses synchronized lyrics (LRC/SRT format) with word-level timing. It tries multiple sources in order of preference and converts plain lyrics to timed format when synced lyrics aren't available.

## Location
`agents/lrc_agent/lrc_agent.py`

## Class: `LRCAgent`

### Configuration
Reads from `config.yaml`:
- `hanit_api.base_url` / `hanit_api.get_song_data` - Hanit API for Spotify synced lyrics

### Dependencies
- `requests` - HTTP API calls
- `beautifulsoup4` - Genius.com scraping
- `lxml` - HTML parsing

### Main Method: `process(meta=None, spotify_url=None, title=None, artist=None)`

**Parameters:**
- `meta` (SongMeta): Song metadata from Audio Agent
- `spotify_url` (str): Spotify track URL (for Hanit API)
- `title` (str): Song title
- `artist` (str): Artist name

**Returns:** `LRCResult` dataclass:
- `success` (bool)
- `lyrics` (List[LyricLine]): Parsed lyric lines with word timing
- `lrc_text` (str): Raw LRC text
- `source` (str): Source name ("hanit_api", "lrclib", "lrclib_search", "genius")
- `error` (str): Error message if failed

### Source Priority (Best to Fallback)
1. **Hanit API** (Spotify synced lyrics) - `GET {base_url}/getLyrics?url={spotify_url}`
2. **LRCLib Direct** - `GET https://lrclib.net/api/get?track_name={title}&artist_name={artist}&duration={duration}`
3. **LRCLib Search** - `GET https://lrclib.net/api/search?q={query}`
4. **Genius.com** (plain text only) - API search + page scrape

### Word-Level Timing Generation
When only line-level timestamps are available (LRC format), the agent creates word-level timing by:
1. Splitting line text into words
2. Estimating duration: `max(1.0, word_count * 0.5)` seconds per line
3. Distributing time evenly across words: `time_per_word = line_duration / word_count`
4. Creating `Word` objects with `start_time` and `end_time`

### Data Structures

**LyricLine:**
```python
@dataclass
class LyricLine:
    id: int                    # Sequential ID
    text: str                  # Full line text
    start_time: float          # Line start (seconds)
    end_time: float            # Line end (seconds) 
    words: List[Word]          # Word-level timing
    translation: str|None      # Optional translation
    roman: str|None            # Optional romanization
    is_duet: bool              # Duet line (right-aligned)
    is_background: bool        # Background vocal line
```

**Word:**
```python
@dataclass
class Word:
    word: str                  # Word text
    start_time: float          # Word start (seconds)
    end_time: float            # Word end (seconds)
```

### LRC Parsing
Regex pattern: `r'\[(\d{2}:\d{2}(?:\.\d{2,3})?)\]'`
- Extracts all timestamps from each line
- Removes timestamps to get clean text
- Uses first timestamp as line start time
- Updates end times based on next line's start time

### Plain Text → LRC Conversion
When only plain lyrics available:
- Splits by newlines
- Estimates ~3 seconds per line
- Generates `[mm:ss.xx]` timestamps

### Usage Example
```python
from agents.lrc_agent import LRCAgent

agent = LRCAgent()
result = agent.process(title="Die With A Smile", artist="Lady Gaga Bruno Mars")
if result.success:
    print(f"Source: {result.source}")
    print(f"Lines: {len(result.lyrics)}")
    for line in result.lyrics[:3]:
        print(f"  [{line.start_time:.2f}] {line.text}")
```

---

## Internal Methods

### `get_from_hanit_api(spotify_url) -> str|None`
Fetches synced lyrics from Hanit API using Spotify URL.

### `get_from_lrclib(title, artist, duration) -> str|None`
Direct LRCLib lookup with track metadata.

### `search_lrclib(query) -> str|None`
Searches LRCLib by combined query string.

### `get_from_genius(title, artist) -> str|None`
Genius API search → page scrape for lyrics.

### `_scrape_genius_page(url) -> str|None`
BeautifulSoup extraction from Genius lyrics containers.

### `_convert_plain_to_lrc(plain_lyrics) -> str`
Converts plain text to LRC with estimated timing.

### `parse_lrc(lrc_text) -> List[LyricLine]`
Main parser - converts LRC text to structured LyricLine objects.

### `_create_word_timing(text, line_start) -> List[Word]`
Distributes line duration evenly across words.

---

## Environment Variables
- `GENIUS_ACCESS_TOKEN` - Genius API token (optional, for higher rate limits)

---

## Testing
```bash
cd /workspaces/hanit/lyric-video-agents
python3 -c "
from agents.lrc_agent import LRCAgent
agent = LRCAgent()
result = agent.process(title='Die With A Smile', artist='Lady Gaga Bruno Mars')
print(f'Success: {result.success}, Source: {result.source}, Lines: {len(result.lyrics) if result.lyrics else 0}')
"
```

---

## Integration Points
- **Called by**: Main pipeline after Audio Agent
- **Consumes**: SongMeta from Audio Agent (title, artist, spotify_url, duration)
- **Feeds**: Video Generator (provides List[LyricLine]), SEO Agent (provides lyrics for timestamps)

---

## Customization
- Add new sources by implementing `get_from_{source}()` methods
- Adjust timing estimation in `_create_word_timing()`
- Modify source priority order in `process()`
- Add caching for repeated song requests
- Support for SRT/VTT formats by adding new parsers