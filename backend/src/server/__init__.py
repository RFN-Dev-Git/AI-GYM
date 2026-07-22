"""HTTP + WebSocket API for AI-GYM — a thin presentation layer over the engine.

The Python backend (engine, counter, validation, analytics) remains the single
source of truth. This package ONLY exposes what already exists:

* ``routes/exercises.py``  — exercise catalogue (straight from the registry)
* ``routes/sessions.py``   — workout history (the exported JSON reports)
* ``routes/settings.py``   — editable subset of the application settings
* ``routes/live.py``       — real-time coaching stream (WebSocket)

Neither the engine, the counting rules, nor the validation logic are modified;
routes compose public behaviour and re-serialize existing artifacts.
"""
