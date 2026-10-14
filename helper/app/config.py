"""Settings loaded from config.yaml and the .env file."""
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

with open(BASE_DIR / "config.yaml", encoding="utf-8") as _f:
    _cfg = yaml.safe_load(_f) or {}

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_TEXT_MODEL = os.getenv("GROQ_TEXT_MODEL", "qwen/qwen3.8-27b")
GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.8-27b")
GROQ_AUDIO_MODEL = os.getenv("GROQ_AUDIO_MODEL", "whisper-large-v3-turbo")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

WATCH_PATHS = [Path(p).expanduser() for p in _cfg.get("watch_paths", [])]
RECURSIVE = bool(_cfg.get("recursive", True))
DRY_RUN = bool(_cfg.get("dry_run", True))
SCAN_EXISTING = bool(_cfg.get("scan_existing", True))
ORGANIZED_FOLDER = _cfg.get("organized_folder", "Organized")
REVIEW_FOLDER = _cfg.get("review_folder", "Needs_Review")
PROTECT_PROJECT_DIRS = bool(_cfg.get("protect_project_dirs", True))
PROJECT_MARKERS = set(_cfg.get("project_markers", []))
IGNORE_DIRS = set(_cfg.get("ignore_dirs", []))
IGNORE_EXTENSIONS = {e.lower() for e in _cfg.get("ignore_extensions", [])}
IGNORE_HIDDEN = bool(_cfg.get("ignore_hidden", True))
ALLOW_EXTERNAL_AI = bool(_cfg.get("allow_external_ai", True))
CONFIDENCE_THRESHOLD = float(_cfg.get("confidence_threshold", 0.75))
MAX_FILE_BYTES = int(_cfg.get("max_file_mb", 50)) * 1024 * 1024

MAX_AUDIO_BYTES = 25 * 1024 * 1024
MAX_TEXT_CHARS = 6000
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Approved folders. The model can only pick from this list.
CATEGORIES = [
    "Receipts", "Finance", "Education", "Work", "Personal", "Legal",
    "Images", "Audio", "Video", "Presentations", "Spreadsheets",
    "Documents", "Code", "Archives", "Other",
]

# Files that are never executed and never sent to an AI model.
BLOCKED_EXT = {
    ".exe", ".dll", ".bin", ".msi", ".bat", ".cmd", ".com", ".scr",
    ".sys", ".so", ".dylib", ".apk", ".jar", ".iso", ".dmg",
}
