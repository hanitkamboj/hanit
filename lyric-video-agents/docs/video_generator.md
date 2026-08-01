# Video Generator Agent Documentation

## Overview
The **Video Generator Agent** creates smooth, high-quality lyric videos (1920x1080 or 4K at 60fps) by rendering animated lyrics over a background image. It uses a custom Pillow-based renderer for frame generation and MoviePy for video encoding.

## Location
`agents/video_generator/video_generator.py` (main)  
`agents/video_generator/renderer.py` (rendering engine)

## Class: `VideoGeneratorAgent`

### Configuration
Reads from `config.yaml`:

**Video Settings:**
- `video.resolution` - "1920x1080" or "3840x2160"
- `video.fps` - 60 (smooth motion)
- `video.codec` - "libx264"
- `video.audio_codec` - "aac"
- `video.bitrate` - "8000k" (high quality)
- `video.preset` - "slow" (better compression)

**Font Settings:**
- `font.family` - "edosz"
- `font.path` - "assets/fonts/edosz.ttf"
- `font.size` - 60px (as requested)
- `font.color` - "#FFFFFF" (white)
- `font.highlight_color` - "#FFD700" (gold)
- `font.shadow_color` - "#000000" (black)
- `font.shadow_offset` - 2px
- `font.shadow_blur` - 4px

**Animation Settings:**
- `animation.scroll_speed` - 0.14 (smooth lerp factor)
- `animation.active_line_scale` - 1.0
- `animation.inactive_line_scale` - 0.97
- `animation.inactive_opacity` - 0.4
- `animation.blur_amount` - 6 (max blur for inactive)
- `animation.transition_duration` - 0.5s

### Dependencies
- `moviepy>=2.0.0` - Video encoding
- `Pillow` - Frame rendering
- `numpy` - Array operations
- `ffmpeg` - Required by MoviePy

### Main Method: `process(audio_path, lyrics, background_path, meta=None)`

**Parameters:**
- `audio_path` (str): Path to .m4a audio file
- `lyrics` (List[LyricLine]): Parsed lyrics with word timing
- `background_path` (str): Path to background image
- `meta` (SongMeta): Optional metadata for filename

**Returns:** `VideoResult` dataclass:
- `success` (bool)
- `video_path` (str): Path to generated .mp4
- `duration` (float): Video duration in seconds
- `error` (str): Error message if failed

### Rendering Pipeline

#### 1. Background Processing (`renderer.create_background()`)
- Loads background image, resizes to target resolution (Lanczos)
- Applies Gaussian blur (radius=20)
- Adds dim overlay (30% black)
- Adds vignette (radial gradient, 55% strength at edges)
- Adds film grain noise texture (5% opacity, overlay blend)

#### 2. Frame Generation (`renderer.render_frame()`)
For each frame (60fps):
- **Find active line**: Binary search for line where `current_time >= line.start_time`
- **Calculate scroll**: Smooth lerp to center active line at 38% screen height
- **Render visible lines**: Lines within viewport + buffer
- **Line styling**:
  - Active line: 100% opacity, scale 1.0, no blur
  - Inactive lines: 40% opacity, scale 0.97, blur up to 6px (distance-based)
  - Duet lines: Right-aligned
- **Word highlighting** (active line only):
  - Progress = `(current_time - word.start) / (word.end - word.start)`
  - Progress 0→1: Base color → Highlight color (gold)
  - Progress ≥1: Highlight color (completed)
  - Smooth color interpolation per frame

#### 3. Video Encoding (`create_video()`)
- Creates `ImageSequenceClip` from PNG frames
- Adds audio with `with_audio()`
- Applies fade in (1s) / fade out (2s) via `FadeIn`/`FadeOut` effects
- Encodes with `write_videofile()`:
  - Codec: libx264
  - Preset: slow (better quality/size)
  - Bitrate: 8000k
  - Threads: 4
  - Pixel format: yuv420p

### Data Flow
```
Audio (duration) → Frame count = duration × 60
For each frame (0 to frame_count-1):
  timestamp = frame / 60
  Render frame at timestamp
  Save as PNG
MoviePy: PNG sequence + Audio → MP4
```

### Usage Example
```python
from agents.video_generator import VideoGeneratorAgent

agent = VideoGeneratorAgent()
result = agent.process(
    audio_path="assets/audio/Lady Gaga - Die With A Smile.m4a",
    lyrics=lyric_lines,  # List[LyricLine] from LRC Agent
    background_path="assets/backgrounds/bg_aesthetic_unsplash.jpg",
    meta=song_meta
)
if result.success:
    print(f"Video: {result.video_path}")
    print(f"Duration: {result.duration:.2f}s")
```

---

## Class: `VideoRenderer` (renderer.py)

### Core Rendering Logic

**`create_background(bg_path) -> Image.Image`**
- Loads, resizes, blurs, dims, vignettes, adds grain
- Returns PIL Image ready for frame compositing

**`render_frame(background, lines, current_time) -> Image.Image`**
- Finds active line index
- Calculates smooth scroll offset (lerp)
- Renders each visible line with:
  - Distance-based opacity/blur/scale
  - Word-level color interpolation
  - Centered horizontal alignment
  - Shadow for readability

**`_render_line_with_words(draw, line, x, y, opacity, current_time)`**
- Iterates through `line.words`
- Calculates progress per word
- Blends base_color → highlight_color based on progress
- Draws shadow + main text

### Animation Parameters (from workspace zip analysis)
```
scroll_speed = 0.14        # Lerp factor for smooth scrolling
active_line_scale = 1.0    # Active line at full size
inactive_line_scale = 0.97 # Slightly smaller inactive lines
inactive_opacity = 0.4     # 40% opacity for non-active
blur_amount = 6            # Max blur radius (px)
transition_duration = 0.5s # Animation transition time
```

These match the "amll" (Apple Music Lyric Library) animation style from the workspace zip.

---

## MoviePy 2.x API Notes
```python
# New imports (MoviePy 2.x)
from moviepy import AudioFileClip, ImageSequenceClip, CompositeVideoClip
from moviepy.video.fx import FadeIn, FadeOut

# New methods
clip = clip.with_audio(audio_clip)  # was set_audio()
clip = clip.with_effects([FadeIn(1.0), FadeOut(2.0)])  # was fadein/fadeout()
```

---

## Performance Considerations
- **Frame generation**: CPU-bound, ~0.5-2s per frame at 1080p
- **Temp storage**: Frames saved to `/tmp/lyric-video-gen/frames/`
- **Cleanup**: Automatic after encoding
- **Parallel**: Not currently parallelized (could use multiprocessing)

---

## Output Specifications
| Setting | Value |
|---------|-------|
| Resolution | 1920×1080 (HD) or 3840×2160 (4K) |
| Frame Rate | 60 fps |
| Codec | H.264 (libx264) |
| Audio | AAC |
| Bitrate | 8000 kbps |
| Preset | slow |
| Pixel Format | yuv420p |

---

## Testing
```bash
cd /workspaces/hanit/lyric-video-agents
# Requires actual audio, lyrics, background files
python3 -c "
from agents.video_generator import VideoGeneratorAgent
agent = VideoGeneratorAgent()
print('Video Generator ready')
print(f'Resolution: {agent.video_settings.resolution.value}')
print(f'FPS: {agent.video_settings.fps}')
"
```

---

## Integration Points
- **Called by**: Main pipeline after Background Agent
- **Consumes**: Audio path, LyricLine list, Background path, SongMeta
- **Feeds**: SEO Agent (provides video for thumbnail), YouTube Uploader (provides video_path)

---

## Customization
- **Resolution**: Change `video.resolution` in config.yaml
- **Font**: Replace `assets/fonts/edosz.ttf` and update `font.path`
- **Colors**: Modify font colors in config.yaml
- **Animation**: Adjust scroll_speed, blur, opacity in config.yaml
- **Background styles**: Add new styles in `renderer.create_background()`
- **Encoding**: Adjust bitrate, preset for quality/speed tradeoff
- **Hardware acceleration**: Add `-hwaccel` flags for NVENC/QSV