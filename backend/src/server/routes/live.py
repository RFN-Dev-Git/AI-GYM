"""Live coaching stream — one WebSocket per workout.

Protocol
--------
Client connects to
``/ws/live?exercise=<key>&source=webcam|video[&video=<ref>]``.

``video`` reference forms (only with ``source=video``):

* ``upload:<id>`` — a video previously uploaded via ``POST /api/uploads``
  (the **web app flow**; ids resolve strictly inside ``uploads/videos/``);
* an explicit path — developer escape hatch / CLI parity (local, single-user);
* omitted — falls back to ``VIDEO_PATH`` from ``.env``.

Server → client::

    binary frame  — one JPEG per processed frame (~capture rate)
    {"type": "state", ...}  — metrics/feedback, ~15 Hz while active
    {"type": "end",  ...}   — workout finished; carries session_id of export
                              and rendered_video when rendering is enabled
    {"type": "error", ...}  — fatal problem (unknown exercise, no camera, ...)

Client → server::

    {"action": "stop"}      — finish now (rep history so far is exported)

Only ONE live session may run at a time (a webcam is a single-user device);
a second connection is rejected with an error event and closed.
"""

import asyncio
import queue
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ...exercises.registry import registry
from ..live_runner import LiveSession
from .uploads import stored_path

router = APIRouter(tags=["live"])

# Single-slot gate. An asyncio.Lock would work too, but the boolean+guard
# lives entirely inside the handler's task — simple and race-free there.
_active_session: Optional[LiveSession] = None


@router.websocket("/ws/live")
async def live_session(websocket: WebSocket, exercise: str, source: str = "webcam", video: Optional[str] = None):
    global _active_session
    await websocket.accept()

    if exercise not in registry.list():
        await websocket.send_json({"type": "error", "message": f"Unknown exercise '{exercise}'"})
        return await websocket.close()
    if source not in ("webcam", "video"):
        await websocket.send_json({"type": "error", "message": "source must be 'webcam' or 'video'"})
        return await websocket.close()

    # Resolve upload references to real paths inside uploads/videos/.
    if video is not None and video.startswith("upload:"):
        upload_id = video[len("upload:"):]
        resolved = stored_path(upload_id)
        if resolved is None:
            await websocket.send_json({"type": "error", "message": f"Unknown upload '{upload_id}'"})
            return await websocket.close()
        video = str(resolved)

    if _active_session is not None and _active_session.is_alive():
        await websocket.send_json({"type": "error", "message": "Another live session is already running"})
        return await websocket.close()

    events: "queue.Queue" = queue.Queue(maxsize=120)
    session = LiveSession(exercise, source, events, video_path=video)
    _active_session = session
    session.start()

    async def forward_events() -> None:
        """Pump runner events to the socket without blocking the loop."""
        loop = asyncio.get_running_loop()
        while True:
            event = await loop.run_in_executor(None, events.get)
            if isinstance(event, (bytes, bytearray)):
                await websocket.send_bytes(bytes(event))
            else:
                await websocket.send_json(event)
                if event.get("type") in ("end", "error"):
                    return

    async def listen_commands() -> None:
        try:
            while True:
                message = await websocket.receive_json()
                if message.get("action") == "stop":
                    session.stop()
        except WebSocketDisconnect:
            session.stop()

    forward = asyncio.create_task(forward_events())
    listen = asyncio.create_task(listen_commands())
    try:
        await asyncio.wait({forward, listen}, return_when=asyncio.FIRST_COMPLETED)
    finally:
        session.stop()
        forward.cancel()
        listen.cancel()
        if _active_session is session:
            _active_session = None
        try:
            await websocket.close()
        except RuntimeError:
            pass  # already closed by the peer
