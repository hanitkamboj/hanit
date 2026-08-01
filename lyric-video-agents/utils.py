"""
Shared utilities for all agents.
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv
from colorama import Fore, Style, init

init(autoreset=True)

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("lyric-video-gen")


def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def get_env(key: str, default: str = None) -> str:
    """Get environment variable"""
    return os.getenv(key, default)


def ensure_dir(path: str) -> None:
    """Ensure directory exists"""
    Path(path).mkdir(parents=True, exist_ok=True)


def print_agent_header(agent_name: str, color: str = Fore.CYAN):
    """Print agent header"""
    print(f"\n{color}{'='*60}")
    print(f"{color}{agent_name.center(60)}")
    print(f"{color}{'='*60}{Style.RESET_ALL}\n")


def format_timestamp(seconds: float) -> str:
    """Convert seconds to MM:SS format"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def format_timestamp_detailed(seconds: float) -> str:
    """Convert seconds to MM:SS.mmm format"""
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:06.3f}"


def parse_timestamp(timestamp: str) -> float:
    """Convert MM:SS or MM:SS.mmm to seconds"""
    parts = timestamp.split(':')
    if len(parts) == 2:
        minutes = int(parts[0])
        seconds = float(parts[1])
        return minutes * 60 + seconds
    elif len(parts) == 3:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    return 0.0


def sanitize_filename(filename: str) -> str:
    """Remove invalid characters from filename"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '')
    return filename.strip()


def get_temp_dir() -> Path:
    """Get temporary directory for processing"""
    temp_dir = Path("/tmp/lyric-video-gen")
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def cleanup_temp_files():
    """Clean up temporary files"""
    import shutil
    temp_dir = get_temp_dir()
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)
