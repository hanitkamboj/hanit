# SEO Agent Documentation

## Overview
The **SEO Agent** generates optimized YouTube metadata (title, description, tags, hashtags, timestamps) following TheCloudLyric channel format and YouTube SEO best practices.

## Location
`agents/seo_agent/seo_agent.py`

## Class: `SEOAgent`

### Configuration
Reads from `config.yaml`:
- `agents.seo_agent.enabled` - true/false
- `agents.seo_agent.generate_timestamps` - true/false
- `agents.seo_agent.optimize_tags` - true/false

### Dependencies
- `requests` + `beautifulsoup4` - For external SEO research (optional)

### Main Method: `process(meta, lines)`

**Parameters:**
- `meta` (SongMeta): Song metadata from Audio Agent
- `lines` (List[LyricLine]): Parsed lyrics from LRC Agent

**Returns:** `SEOResult` dataclass:
- `success` (bool)
- `seo_data` (SEOData): Complete metadata package
- `error` (str): Error message if failed

### SEOData Structure
```python
@dataclass
class SEOData:
    title: str                    # Video title
    description: str              # Full description with lyrics, timestamps, CTA
    tags: List[str]               # YouTube tags (max 30)
    hashtags: List[str]           # Hashtags for description
    timestamps: Dict[str, str]    # Section → MM:SS mapping
    thumbnail_path: str|None      # Optional thumbnail path
```

---

## Title Generation
**Format:** `{Artist} - {Song Title} (Lyrics)`

Example: `Lady Gaga & Bruno Mars - Die With A Smile (Lyrics)`

Optimized for:
- Search: Contains artist + title + "Lyrics"
- Click-through: Clear format, recognizable
- Algorithm: Keywords at start

---

## Description Generation
Follows TheCloudLyric template exactly:

```
{Artist} - {Title} (Lyrics)

🎵 Enjoy the lyric video for "{Title}" by {Artist} — [album context].

Full lyrics on screen throughout — perfect for singing along, 
learning the words, or just vibing to the music.

🎧 Song: {Title}
🎤 Artist(s): {Artist}
📅 Released: {Date}
💿 Album: {Album}
🎹 Genre: {Genre}
🏷️ Label: {Label}

LYRICS:

[Full lyrics with section headers]

⏱️ TIMESTAMPS
00:00 Intro
00:29 Verse 1
...

👍 If you enjoyed this lyric video, leave a like and subscribe 
for more lyrics videos from {Artist} and similar artists!
🔔 Turn on notifications so you don't miss the next upload.
💬 Drop your favorite line from the song in the comments below.

📲 Follow us:
Instagram: https://www.instagram.com/_.h.a.rsh._/

⚠️ This is a fan-made lyrics video created for entertainment 
purposes. All rights to "{Title}" belong to {Artist}.

#{Hashtags}
```

---

## Timestamp Generation
Automatically detects song sections from lyric text:

| Section | Keywords |
|---------|----------|
| Intro | "intro", "introduction" |
| Verse 1/2/3 | "verse 1", "verse 2", "verse" |
| Pre-Chorus | "pre-chorus", "pre chorus" |
| Chorus | "chorus" |
| Bridge | "bridge" |
| Outro | "outro", "ending" |
| Post-Chorus | "post-chorus", "post chorus" |
| Hook | "hook" |
| Instrumental | "instrumental", "break" |

Algorithm:
1. Iterates through LyricLine objects
2. Checks `line.text.lower()` for section keywords
3. Records first occurrence of each section with `format_timestamp(line.start_time)`
4. Falls back to Start/Middle/End if no sections found

---

## Tag Generation
Generates up to 30 YouTube tags:

**Core tags (always):**
- `{Artist}`
- `{Title}`
- `{Artist} {Title}`
- `{Title} lyrics`
- `{Artist} lyrics`
- `{Title} lyric video`
- `{Artist} {Title} lyrics`
- `{Title} official lyrics`
- `{Title} song lyrics`

**Contextual tags:**
- `{Album} album` (if album)
- `{Artist} {Album}` (if album)
- `{Genre} lyrics` (if genre)
- `{Genre} music` (if genre)

**Discovery tags:**
- `{Artist} new song`
- `{Title} audio`
- `{Title} karaoke`
- `lyrics video`
- `lyric video`
- `song lyrics`

---

## Hashtag Generation
Generates up to 15 hashtags for description:

- `#{ArtistNoSpaces}` (e.g., #LadyGagaBrunoMars)
- `#{TitleNoSpaces}` (e.g., #DieWithASmile)
- `#{GenreNoSpaces}` (if genre)
- `#Lyrics`
- `#LyricVideo`
- `#Music`

---

## External SEO Research (Optional)
The `search_song_info()` method is a placeholder for:
- Spotify API: release date, popularity, genres
- Last.fm: tags, similar artists
- MusicBrainz: recording metadata
- YouTube search: competing videos, keyword analysis

---

## Usage Example
```python
from agents.seo_agent import SEOAgent
from models import SongMeta, LyricLine

agent = SEOAgent()
meta = SongMeta(
    title="Die With A Smile",
    artist="Lady Gaga & Bruno Mars",
    album="Mayhem",
    release_date="August 16, 2024",
    genre="Pop"
)
lines = [LyricLine(id=0, text="I just woke up...", start_time=10.0, words=[])]

result = agent.process(meta, lines)
if result.success:
    seo = result.seo_data
    print(f"Title: {seo.title}")
    print(f"Tags: {len(seo.tags)} tags")
    print(f"Description length: {len(seo.description)} chars")
```

---

## Output Files
Pipeline saves SEO data as JSON:
```
assets/output/{Artist} - {Title} (Lyrics)_seo.json
```

Contains:
```json
{
  "title": "...",
  "description": "...",
  "tags": [...],
  "hashtags": [...],
  "timestamps": {...}
}
```

---

## Testing
```bash
cd /workspaces/hanit/lyric-video-agents
python3 -c "
from agents.seo_agent import SEOAgent
from models import SongMeta, LyricLine, Word

agent = SEOAgent()
meta = SongMeta(title='Test Song', artist='Test Artist', genre='Pop')
lines = [LyricLine(id=0, text='Test lyrics', start_time=0, words=[])]
result = agent.process(meta, lines)
print(f'Success: {result.success}')
if result.success:
    print(f'Title: {result.seo_data.title}')
    print(f'Tags: {result.seo_data.tags[:5]}')
"
```

---

## Integration Points
- **Called by**: Main pipeline after Video Generator
- **Consumes**: SongMeta, List[LyricLine]
- **Feeds**: YouTube Uploader (provides SEOData), saves JSON for reuse

---

## Customization
- **Description template**: Modify `generate_description()` method
- **Tag strategy**: Adjust `generate_tags()` for niche keywords
- **Section detection**: Add more keywords to `section_keywords` dict
- **CTA text**: Customize call-to-action phrases
- **Social links**: Update `generate_description()` with your links
- **Disclaimer**: Modify copyright disclaimer text
- **Language**: Support multi-language descriptions