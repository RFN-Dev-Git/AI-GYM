"""FastAPI application factory — the single entry point for the AI-GYM API.

Routers are mounted under ``/api`` (versioned paths can be introduced later
without moving handlers). CORS is open to local dev origins (Vite on :5173
and :4173); tighten for real deployments via a reverse proxy.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import downloads, exercises, live, sessions, settings as settings_routes, uploads


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI-GYM API",
        description="Pose-estimation gym trainer — session analytics and live coaching.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok"}

    app.include_router(exercises.router, prefix="/api")
    app.include_router(sessions.router, prefix="/api")
    app.include_router(settings_routes.router, prefix="/api")
    app.include_router(uploads.router, prefix="/api")
    app.include_router(downloads.router, prefix="/api")
    app.include_router(live.router)
    return app


app = create_app()
