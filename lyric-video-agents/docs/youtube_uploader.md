# YouTube Uploader Agent Documentation

## Overview
The **YouTube Uploader Agent** handles authentication and video upload to YouTube using the YouTube Data API v3. Supports metadata, thumbnails, and privacy settings.

## Location
`agents/youtube_uploader/youtube_uploader.py`

## Class: `YouTubeUploaderAgent`

### Configuration
Reads from `config.yaml`:

**YouTube Settings:**
- `youtube.category` - "10" (Music category)
- `youtube.privacy_status` - "public", "private", or "unlisted"
- `youtube.auto_upload` - false (disabled by default)
- `api.youtube_client_secrets` - Path to client_secrets.json

### Dependencies
- `google-api-python-client` - YouTube Data API
- `google-auth-oauthlib` - OAuth 2.0 flow
- `google-auth-httplib2` - HTTP transport

### Setup Requirements

#### 1. Google Cloud Console
1. Go to https://console.cloud.google.com/
2. Create/select project
3. Enable **YouTube Data API v3**
4. Create **OAuth 2.0 Client ID** (Desktop app)
5. Download `client_secrets.json` to project root

#### 2. OAuth Scopes
```
https://www.googleapis.com/auth/youtube.upload
```

#### 3. First Run
On first upload, browser opens for Google account authorization.
Token saved to `token.json` for subsequent runs.

---

## Main Method: `process(video_path, seo_data, thumbnail_path=None, auto_upload=None)`

**Parameters:**
- `video_path` (str): Path to .mp4 video file
- `seo_data` (SEOData): Metadata from SEO Agent
- `thumbnail_path` (str): Optional custom thumbnail
- `auto_upload` (bool): Override config setting

**Returns:** `UploadResult` dataclass:
- `success` (bool)
- `video_id` (str|None): YouTube video ID
- `video_url` (str|None): Full YouTube URL
- `error` (str): Error message if failed

### Upload Process
1. **Authenticate**: Load/refresh OAuth credentials
2. **Build service**: `build('youtube', 'v3', credentials=creds)`
3. **Prepare body**: Snippet + Status from SEOData
4. **Resumable upload**: `MediaFileUpload` with 10MB chunks
5. **Progress tracking**: Logs upload percentage
6. **Thumbnail upload**: Optional separate API call
7. **Return**: Video ID and URL

### Metadata Mapping
```python
body = {
    'snippet': {
        'title': seo_data.title,              # Max 100 chars
        'description': seo_data.description,   # Max 5000 chars
        'tags': seo_data.tags,                # Max 500 chars total
        'categoryId': '10',                   # Music
    },
    'status': {
        'privacyStatus': 'public',            # or private/unlisted
        'selfDeclaredMadeForKids': False,
    }
}
```

### Usage Example
```python
from agents.youtube_uploader import YouTubeUploaderAgent
from agents.seo_agent import SEOAgent

uploader = YouTubeUploaderAgent()
seo_agent = SEOAgent()

# Generate SEO data
seo_result = seo_agent.process(meta, lyrics)

# Upload (auto_upload=True or pass auto_upload=True)
upload_result = uploader.process(
    video_path="assets/output/Video.mp4",
    seo_data=seo_result.seo_data,
    thumbnail_path="assets/output/thumb.jpg",
    auto_upload=True
)

if upload_result.success:
    print(f"Video: {upload_result.video_url}")
```

---

## CLI Usage
```bash
# From project root with pipeline
python3 pipeline.py --query "Song Name" --upload

# Or manually
python3 -c "
from agents.youtube_uploader import YouTubeUploaderAgent
uploader = YouTubeUploaderAgent()
# Requires video file and SEO data
"
```

---

## Internal Methods

### `get_credentials() -> Credentials`
- Loads `token.json` if exists
- Refreshes expired tokens
- Runs OAuth flow if needed
- Saves new tokens

### `build_service() -> Resource`
Creates authenticated YouTube API client.

### `upload_video(video_path, seo_data, thumbnail_path) -> UploadResult`
Main upload logic with resumable upload and progress logging.

### `_upload_thumbnail(youtube, video_id, thumbnail_path)`
Uploads custom thumbnail via `thumbnails().set()`.

---

## Error Handling
| Error | Cause | Resolution |
|-------|-------|------------|
| `FileNotFoundError: client_secrets.json` | Missing OAuth credentials | Download from Google Cloud Console |
| `HttpError 403: quotaExceeded` | Daily upload quota exceeded | Wait 24h or request quota increase |
| `HttpError 400: invalidVideoMetadata` | Title/description too long | Truncate to limits |
| `HttpError 401: unauthorized` | Token expired/revoked | Delete `token.json`, re-authenticate |

---

## YouTube Limits
| Limit | Value |
|-------|-------|
| Title | 100 characters |
| Description | 5000 characters |
| Tags | 500 characters total |
| Hashtags | 15 max in description |
| Daily uploads | ~6 videos (default quota) |
| Video size | 256 GB / 12 hours |
| Thumbnail | 2MB max, 1280x720 min |

---

## Testing
```bash
cd /workspaces/hanit/lyric-video-agents
# First run requires browser auth
python3 -c "
from agents.youtube_uploader import YouTubeUploaderAgent
uploader = YouTubeUploaderAgent()
print('Uploader ready')
print(f'Privacy: {uploader.privacy_status}')
print(f'Category: {uploader.category_id}')
"
```

---

## Integration Points
- **Called by**: Main pipeline (if `auto_upload=True` or `--upload` flag)
- **Consumes**: Video path, SEOData, optional thumbnail
- **Feeds**: Nothing (terminal agent)

---

## Security Notes
- **Never commit** `client_secrets.json` or `token.json` to git
- Add to `.gitignore`:
  ```
  client_secrets.json
  token.json
  ```
- Use separate Google Cloud project for production
- Monitor quota usage in Cloud Console

---

## Customization
- **Privacy**: Change `youtube.privacy_status` in config.yaml
- **Category**: Modify `youtube.category` (see YouTube categories list)
- **Playlist**: Add `playlistId` to snippet for auto-playlist
- **Location**: Add `recordingDetails.location` for geo-tagging
- **Language**: Add `defaultLanguage` / `defaultAudioLanguage`
- **Scheduled**: Set `publishAt` for scheduled publishing
- **Notifications**: Subscribe to `video.status.uploadStatus` for webhooks