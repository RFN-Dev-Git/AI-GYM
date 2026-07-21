"""Application settings (pydantic-settings) with project-root-relative paths.

All filesystem paths are exposed as :class:`pathlib.Path` objects and resolved
relative to the project root, so the application behaves identically no matter
which directory it is launched from. The shared root/path constants live here
so paths are never scattered as ad-hoc strings across the codebase.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ── Project-root path constants ────────────────────────────────────────────
# Derived from this file's location, so they are independent of the CWD.
#   src/config/app_settings.py -> parents[2] == project root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = PROJECT_ROOT / "assets"
MODELS_DIR = ASSETS_DIR / "models"
VIDEOS_DIR = ASSETS_DIR / "videos"
OUTPUT_DIR = PROJECT_ROOT / "output"


def _abs_path(path) -> Path:
    """Resolve a (possibly relative) path against the project root."""
    path = Path(path)
    return path if path.is_absolute() else PROJECT_ROOT / path


class AppSettings(BaseSettings):
    # Paths are Path objects; relative strings are resolved against PROJECT_ROOT.
    MODEL_PATH: Path
    VIDEO_PATH: Optional[Path] = None

    DISPLAY_MAX_WIDTH: int = 1280

    USE_WEBCAM: bool = False
    WEBCAM_INDEX: int = 0

    SAVE_OUTPUT: bool = False
    OUTPUT_PATH: Path = OUTPUT_DIR / "result.mp4"

    # Session analytics: frame rate used to turn per-repetition frame spans
    # into durations (seconds) in the generated SessionSummary.
    ANALYTICS_FPS: float = 25.0

    # Session analytics export (opt-in). When EXPORT_SESSION is true the engine
    # persists a SessionSummary (produced by the analytics module) after a run.
    EXPORT_SESSION: bool = False
    EXPORT_FORMAT: str = "json"   # "json" | "csv"
    EXPORT_DIR: Path = PROJECT_ROOT / "sessions"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def _resolve_relative_paths(self) -> "AppSettings":
        """Resolve MODEL_PATH / VIDEO_PATH / OUTPUT_PATH against PROJECT_ROOT.

        An empty VIDEO_PATH (e.g. an empty env var) is normalised to ``None``.
        """
        self.MODEL_PATH = _abs_path(self.MODEL_PATH)
        if self.VIDEO_PATH is not None:
            # An empty env value coerces to Path(".") -> treat as unset.
            if str(self.VIDEO_PATH).strip() in ("", "."):
                self.VIDEO_PATH = None
            else:
                self.VIDEO_PATH = _abs_path(self.VIDEO_PATH)
        self.OUTPUT_PATH = _abs_path(self.OUTPUT_PATH)
        self.EXPORT_DIR = _abs_path(self.EXPORT_DIR)
        return self


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()


settings = get_settings()
