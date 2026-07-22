"""Exercise catalogue endpoints — derived straight from the registry."""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from ...exercises.exercise import Exercise
from ...exercises.registry import registry

router = APIRouter(prefix="/exercises", tags=["exercises"])


def _exercise_payload(key: str, ex: Exercise) -> Dict[str, Any]:
    """One exercise, using ONLY data that genuinely exists (no invented fields).

    ``image`` is a forward slot for real thumbnails/photos (null today);
    the frontend renders a placeholder for it.
    """
    return {
        "id": key,
        "name": ex.name,
        "description": ex.metadata.description,
        "muscle_groups": list(ex.metadata.muscle_groups),
        "camera": str(getattr(ex.camera, "value", ex.camera)),
        "counters": [c.name for c in ex.counter_rules],
        "rules": len(ex.validation_rules),
        "image": None,
    }


@router.get("")
def list_exercises() -> List[Dict[str, Any]]:
    return [_exercise_payload(key, registry.get(key)) for key in registry.list()]


@router.get("/{key}")
def get_exercise(key: str) -> Dict[str, Any]:
    if not registry.exists(key):
        raise HTTPException(status_code=404, detail=f"Unknown exercise '{key}'")
    return _exercise_payload(key, registry.get(key))
