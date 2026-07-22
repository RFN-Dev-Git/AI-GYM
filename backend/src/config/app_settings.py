"""Application settings (pydantic-settings) with project-relative paths.

All filesystem paths are exposed as :class:`pathlib.Path` objects and resolved
against a fixed base, so the application behaves identically no matter which
directory it is launched from. The shared root/path constants live here so
paths are never scattered as ad-hoc strings across the codebase.

Path bases
----------
``PROJECT_ROOT`` (the ``backend/`` package root)
    code + configuration (``.env``) only.
``REPO_ROOT`` (the repository root, ``PROJECT_ROOT``'s parent)
    every *data* path. Inputs live in ``assets/`` (pose model, dev videos),
    generated artifacts in ``output/`` (``sessions/`` = exported reports,
    ``videos/`` = rendered sessions), user-uploaded videos in
    ``uploads/videos/``.

**Rule:** every relative path in ``backend/.env`` resolves against
``REPO_ROOT``; absolute paths pass through untouched. The ``.env`` file
itself is located by absolute path (``<backend>/.env``) — never by CWD.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ── Root path constants ────────────────────────────────────────────────────
# Derived from this file's location, so they are independent of the CWD.
#   src/config/app_settings.py -> parents[2] == backend package root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PROJECT_ROOT.parent

# Inputs (repo root): pose model + developer sample videos.
ASSETS_DIR = REPO_ROOT / "assets"
MODELS_DIR = ASSETS_DIR / "models"
VIDEOS_DIR = ASSETS_DIR / "videos"

# Generated artifacts (repo root): reports, rendered videos.
OUTPUT_DIR = REPO_ROOT / "output"
SESSIONS_DIR = OUTPUT_DIR / "sessions"
RENDERED_DIR = OUTPUT_DIR / "videos"

# User uploads (repo root, deliberately separate from assets AND output):
# videos the web app receives from its users.
UPLOADS_DIR = REPO_ROOT / "uploads" / "videos"


def resolve_path(path, base: Path = REPO_ROOT) -> Path:
    """Resolve a (possibly relative) path against ``base`` (repo root)."""
    path = Path(path)
    return path if path.is_absolute() else base / path


class AppSettings(BaseSettings):
    # Paths are Path objects; relative strings are resolved against PROJECT_ROOT.
    MODEL_PATH: Path
    VIDEO_PATH: Optional[Path] = None

    DISPLAY_MAX_WIDTH: int = 1280

    USE_WEBCAM: bool = False
    WEBCAM_INDEX: int = 0

    SAVE_OUTPUT: bool = False
    OUTPUT_PATH: Path = RENDERED_DIR / "result.mp4"

    # Session analytics: frame rate used to turn per-repetition frame spans
    # into durations (seconds) in the generated SessionReport.
    ANALYTICS_FPS: float = 25.0

    # Session analytics export (opt-in). When EXPORT_SESSION is true the engine
    # persists a complete SessionReport (produced by the analytics module) as a
    # single JSON document after a run. EXPORT_FORMAT is kept only for .env
    # backward compatibility: JSON is now the sole export format (a complete
    # session history cannot be flattened to CSV without losing information),
    # and any other value is ignored with a console note.
    EXPORT_SESSION: bool = False
    EXPORT_FORMAT: str = "json"   # legacy; JSON is always used
    EXPORT_DIR: Path = SESSIONS_DIR

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",   # absolute: independent of the CWD
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def _resolve_relative_paths(self) -> "AppSettings":
        """Resolve any relative .env path against ``REPO_ROOT``.

        An empty VIDEO_PATH (e.g. an empty env var) is normalised to ``None``.
        """
        self.MODEL_PATH = resolve_path(self.MODEL_PATH)
        if self.VIDEO_PATH is not None:
            # An empty env value coerces to Path(".") -> treat as unset.
            if str(self.VIDEO_PATH).strip() in ("", "."):
                self.VIDEO_PATH = None
            else:
                self.VIDEO_PATH = resolve_path(self.VIDEO_PATH)
        self.OUTPUT_PATH = resolve_path(self.OUTPUT_PATH)
        self.EXPORT_DIR = resolve_path(self.EXPORT_DIR)
        return self


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()


settings = get_settings()
