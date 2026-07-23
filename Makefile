.PHONY: run backend frontend test build help

EXERCISE ?= hack_squat
VIDEO ?= hackw.mp4

# ── Engine CLI (developer desktop path, OpenCV window) ─────────────────────
# VIDEO may be a bare file name (looked up in assets/videos/), a path relative
# to backend/, or an absolute path. Requires assets/videos/<clip> plus the
# pose model at MODEL_PATH (backend/.env). Relative paths in .env resolve
# against the repository root.
run:
	clear
	cd backend && uv run python -m src.main $(EXERCISE) assets/videos/$(VIDEO)

# ── Full stack (web app: uploads + live coaching over WebSocket) ───────────
backend:    ## API + WebSocket server on :8000  (the React app talks to this)
	clear
	cd backend && uv run uvicorn src.server.app:app --reload --port 8000

frontend:   ## Vite dev server on :5173 (proxies /api + /ws to :8000)
	clear
	cd frontend && npm run dev

build:      ## frontend typecheck + production bundle (frontend/dist)
	cd frontend && npm run build

test:       ## all backend test suites
	cd backend && python tests/analytics/test_session_report.py && \
	python tests/exercises/test_hack_squat.py && \
	python tests/services/test_distance_handling.py && \
	python tests/services/test_video_source.py && \
	python tests/integration/test_architecture.py


code:
	./codex -ext .py

help:
	@echo "  run       - engine CLI:        make run EXERCISE=<name> VIDEO=<file|path>"
	@echo "  backend   - FastAPI + WS:      make backend   (was: make serve)"
	@echo "  frontend  - Vite dev server:   make frontend  (was: make dev)"
	@echo "  build     - frontend build:    make build"
	@echo "  test      - backend suites:    make test"
