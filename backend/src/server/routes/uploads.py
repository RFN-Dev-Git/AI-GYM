"""Video uploads — the web app's way to pick a workout video.

Browser uploads land in the repo-root ``uploads/videos/`` directory under a
name the server controls::

    <uuid12>__<sanitized-original-name>.<ext>

The returned ``id`` IS that stored filename. The WebSocket live endpoint
references an upload as ``video=upload:<id>`` — clients never hand the server
an arbitrary filesystem path (``_SAFE_STORED_NAME`` + the uploads-dir lookup
make traversal attempts resolve to "unknown upload").

Uploads are cleaned up manually via DELETE (no TTL/GC yet — local single-user
deployment).
"""

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile

from ...config import UPLOADS_DIR

router = APIRouter(prefix="/uploads", tags=["uploads"])

_ALLOWED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}
_MAX_UPLOAD_BYTES = 1024 * 1024 * 1024  # 1 GiB
_CHUNK = 1024 * 1024

#: What an upload id (the stored filename) is allowed to look like.
_SAFE_STORED_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,180}$")


def _sanitize_original(name: str) -> str:
    """Keep the original name recognizable but filesystem- and URL-safe."""
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(name).stem).strip("._-")
    return stem[:60] or "video"


def stored_path(upload_id: str) -> Optional[Path]:
    """Resolve an upload id to an existing file inside the uploads dir.

    Returns ``None`` for anything malformed or absent — never a path outside
    the uploads directory.
    """
    if not _SAFE_STORED_NAME.match(upload_id) or ".." in upload_id:
        return None
    path = UPLOADS_DIR / upload_id
    return path if path.is_file() else None


def _describe(path: Path) -> Dict[str, Any]:
    name = path.name
    original = name.split("__", 1)[1] if "__" in name else name
    return {
        "id": name,
        "name": original,
        "size": path.stat().st_size,
        "uploaded_at": datetime.fromtimestamp(
            path.stat().st_mtime, tz=timezone.utc
        ).isoformat(),
    }


@router.get("")
def list_uploads() -> List[Dict[str, Any]]:
    """Previously uploaded videos, newest first."""
    if not UPLOADS_DIR.is_dir():
        return []
    files = (p for p in UPLOADS_DIR.iterdir() if p.is_file() and _SAFE_STORED_NAME.match(p.name))
    return [_describe(p) for p in sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)]


@router.post("", status_code=201)
async def upload_video(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Store one uploaded video; returns the id used to start a live session."""
    original = file.filename or "video"
    ext = Path(original).suffix.lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{ext or 'none'}' — allowed: {', '.join(sorted(_ALLOWED_EXTENSIONS))}",
        )

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    stored = f"{uuid.uuid4().hex[:12]}__{_sanitize_original(original)}{ext}"
    dest = UPLOADS_DIR / stored

    size = 0
    try:
        with dest.open("wb") as fh:
            while chunk := await file.read(_CHUNK):
                size += len(chunk)
                if size > _MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="File too large (max 1 GiB)")
                fh.write(chunk)
    except Exception:
        dest.unlink(missing_ok=True)
        raise

    if size == 0:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="Empty file")

    return {"id": stored, "name": _describe(dest)["name"], "size": size}


@router.delete("/{upload_id}", status_code=204)
def delete_upload(upload_id: str) -> None:
    path = stored_path(upload_id)
    if path is None:
        raise HTTPException(status_code=404, detail=f"Unknown upload '{upload_id}'")
    path.unlink()
