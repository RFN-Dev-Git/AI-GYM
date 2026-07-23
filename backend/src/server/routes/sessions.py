"""Workout history endpoints — the exported JSON reports, served as-is."""

from dataclasses import asdict
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from ..store import SessionStore

router = APIRouter(prefix="/sessions", tags=["sessions"])
_store = SessionStore()


@router.get("")
def list_sessions() -> List[Dict[str, Any]]:
    """Session list items, newest first."""
    return [asdict(item) for item in _store.list()]


@router.get("/{session_id}")
def get_session(session_id: str) -> Dict[str, Any]:
    """The complete session report document (verbatim export)."""
    report = _store.get(session_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Unknown session '{session_id}'")
    return report


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: str) -> None:
    if not _store.delete(session_id):
        raise HTTPException(status_code=404, detail=f"Unknown session '{session_id}'")
