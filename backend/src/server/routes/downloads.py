"""Downloads of generated artifacts (rendered session videos).

One deliberately narrow endpoint: files that already live inside the repo-root
``output/videos/`` directory, addressed by bare filename only.
"""

import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ...config import RENDERED_DIR

router = APIRouter(prefix="/downloads", tags=["downloads"])

_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,180}\.mp4$")


@router.get("/rendered/{name}")
def download_rendered_video(name: str) -> FileResponse:
    """Serve a rendered/annotated session video produced by a live run."""
    if not _SAFE_NAME.match(name) or ".." in name:
        raise HTTPException(status_code=404, detail=f"Unknown video '{name}'")
    path = RENDERED_DIR / name
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"Unknown video '{name}'")
    return FileResponse(path, media_type="video/mp4", filename=name)
