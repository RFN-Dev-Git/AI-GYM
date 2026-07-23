"""Editable application settings (safe subset) — runtime + .env persistence.

Only operational knobs are exposed; exercise rules, thresholds and any
counting/validation configuration are deliberately NOT editable through the
API (configs remain code, versioned with the backend).
"""

import re
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...config import PROJECT_ROOT, REPO_ROOT, resolve_path, settings

router = APIRouter(prefix="/settings", tags=["settings"])
_ENV_PATH = PROJECT_ROOT / ".env"


def _display_path(path: Path) -> str:
    """Serialize a path .env-style: repo-root-relative (``assets/…``,
    ``output/…``) when possible, otherwise absolute. This mirrors the
    AppSettings validator, which resolves every relative path against the
    repository root."""
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()

#: key -> (kind). Paths are stored .env-style (relative to the backend root).
_EDITABLE: Dict[str, str] = {
    "USE_WEBCAM": "bool",
    "WEBCAM_INDEX": "int",
    "VIDEO_PATH": "path",
    "MODEL_PATH": "path",
    "SAVE_OUTPUT": "bool",
    "OUTPUT_PATH": "path",
    "ANALYTICS_FPS": "float",
    "DISPLAY_MAX_WIDTH": "int",
    "EXPORT_SESSION": "bool",
}


class SettingsPatch(BaseModel):
    """Partial settings update (only editable keys, already typed)."""

    model_config = {"extra": "forbid"}

    USE_WEBCAM: bool | None = None
    WEBCAM_INDEX: int | None = None
    VIDEO_PATH: str | None = None
    MODEL_PATH: str | None = None
    SAVE_OUTPUT: bool | None = None
    OUTPUT_PATH: str | None = None
    ANALYTICS_FPS: float | None = None
    DISPLAY_MAX_WIDTH: int | None = None
    EXPORT_SESSION: bool | None = None


def _serialize_value(key: str, value: Any) -> str:
    kind = _EDITABLE[key]
    if kind == "bool":
        return "true" if value else "false"
    if kind == "path":
        return _display_path(Path(value))
    return str(value)


def _current() -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    for key, kind in _EDITABLE.items():
        value = getattr(settings, key)
        if isinstance(value, Path):
            value = _display_path(value)
        data[key] = value
    return data


def _persist_env(updates: Dict[str, Any]) -> None:
    """Rewrite/update KEY=VALUE lines in .env, preserving everything else."""
    rendered = {key: _serialize_value(key, value) for key, value in updates.items()}
    lines = _ENV_PATH.read_text(encoding="utf-8").splitlines() if _ENV_PATH.exists() else []
    seen = set()
    pattern = re.compile(r"^\s*([A-Z0-9_]+)\s*=")
    out = []
    for line in lines:
        match = pattern.match(line)
        if match and match.group(1) in rendered:
            key = match.group(1)
            out.append(f"{key}={rendered[key]}")
            seen.add(key)
        else:
            out.append(line)
    for key, value in rendered.items():
        if key not in seen:
            out.append(f"{key}={value}")
    _ENV_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")


@router.get("")
def get_settings() -> Dict[str, Any]:
    return _current()


@router.put("")
def update_settings(patch: SettingsPatch) -> Dict[str, Any]:
    updates = patch.model_dump(exclude_none=True)
    if not updates:
        return _current()
    if "ANALYTICS_FPS" in updates and updates["ANALYTICS_FPS"] <= 0:
        raise HTTPException(status_code=422, detail="ANALYTICS_FPS must be positive")
    # Apply to the live settings object first (Path coercion kept intact).
    # Relative paths are resolved against the repo root here because
    # assignment does not re-run the AppSettings validator — the engine must
    # always see absolute paths regardless of the server's CWD.
    for key, value in updates.items():
        current = getattr(settings, key)
        if isinstance(current, Path):
            value = resolve_path(value)
        setattr(settings, key, value)
    # ...then persist for future runs.
    try:
        _persist_env(updates)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not write .env: {exc}")
    return _current()
