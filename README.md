# AI-GYM — Intelligent Coaching Platform

Real-time pose-estimation gym trainer: a production-style **full-stack** app with
a Python analytics engine (source of truth) and a dark-first React coaching UI.

- **Live coaching** — webcam/video streamed with skeleton overlay, rep counts,
  stages, angles, live form score and per-rule feedback over WebSocket.
- **Session reports** — every workout is exported as a normalized JSON report
  and rendered as score rings, charts, rule statistics and expandable rep breakdowns.
- **History & analytics** — searchable/sortable workout history, progress trends,
  most-common-mistake tracking on the dashboard.

## Architecture

```
AI-GYM/
├── assets/                 # runtime inputs (repo root)
│   ├── models/             #   pose landmarker .task (required — see assets/README.md)
│   └── videos/             #   developer sample clips (engine CLI only)
│
├── uploads/                # user uploads (repo root, separate from assets)
│   └── videos/             #   videos uploaded through the web app
│
├── output/                 # generated artifacts (repo root)
│   ├── sessions/           #   exported JSON session reports
│   └── videos/             #   rendered/annotated session videos
│
├── docs/                   # all architecture / design documentation
│
├── backend/                # Python — the product's source of truth
│   ├── src/
│   │   ├── exercises/      # pure exercise configuration (rules as data)
│   │   ├── services/       # GymEngine, RepCounter, RepJudge (UNTOUCHED logic)
│   │   ├── analytics/      # SessionAnalyzer → SessionReport → JSON export
│   │   ├── core/  utils/  config/
│   │   └── server/         # thin FastAPI + WebSocket layer over the engine
│   ├── tests/              # behavior suites by topic (analytics/ exercises/
│   │                       #   services/ integration/ — run via make test)
│   └── .env  requirements.txt
│
├── frontend/               # React 18 + TypeScript + Vite
│   └── src/
│       ├── schemas/        # shared data models (mirror backend exactly)
│       ├── lib/            # typed API client, formatters, utils
│       ├── components/     # shadcn-style primitives + app shell
│       ├── features/       # dashboard · exercises · live · history · report · settings
│       └── providers/      # theme (dark-first), toasts, react-query
│
└── Makefile                # run · backend · frontend · build · test
```

Design law: **no logic lives in the frontend.** Counting, validation, scoring,
and judging stay in the Python engine; the API re-serializes existing artifacts
and the UI renders them. The engine loop is reused, not rewritten.

## Quick start

```bash
# 0. pose model (once) — place pose_landmarker_full.task in assets/models/

# 1. backend deps (once), then the API + WS server
cd backend && pip install -r requirements.txt
make backend                    # http://localhost:8000  (/api/*, /ws/live)

# 2. frontend (once), then the app
cd frontend && npm install
make frontend                   # http://localhost:5173  (proxies /api + /ws)
```

Open http://localhost:5173, pick an exercise, choose **webcam** or **video**
(upload a clip straight from your computer), press **Start workout**. The full
report opens automatically when the workout ends; a rendered (annotated) video
is downloadable when `SAVE_OUTPUT=true`.

### Engine CLI (developer desktop mode)

```bash
make run EXERCISE=hack_squat VIDEO=hackw.mp4
# VIDEO may be a bare file name (looked up in assets/videos/),
# a relative path, or an absolute path. Requires the clip to exist plus the
# pose model at MODEL_PATH (backend/.env, e.g. assets/models/pose_landmarker_full.task).
```

### Tests & build

```bash
make test     # backend behavior suites
make build    # typecheck + production bundle of the frontend
```

## Docs

- `docs/ARCHITECTURE.md` — engine design (rules as configuration)
- `docs/ADDING_AN_EXERCISE.md` — how to add a coached exercise
- `docs/FRONTEND_ARCHITECTURE.md` — complete frontend reference
- Session report JSON contract — see `backend/src/analytics/` and `frontend/src/schemas/`

## Communicating with the backend

| Channel | Purpose |
|---|---|
| `GET  /api/exercises` | exercise catalogue (from the registry) |
| `GET  /api/sessions` / `GET /api/sessions/{id}` | workout history / full report |
| `DELETE /api/sessions/{id}` | delete a report |
| `GET/PUT /api/settings` | editable runtime settings (.env-backed) |
| `POST /api/uploads` | upload a workout video (web app flow) → `{id}` |
| `GET  /api/uploads` / `DELETE /api/uploads/{id}` | list / delete uploads |
| `GET  /api/downloads/rendered/{name}` | download a rendered session video |
| `WS   /ws/live?exercise=&source=webcam\|video[&video=upload:<id>]` | live stream: binary JPEG frames + JSON state, `{"action":"stop"}` to finish |

Built to grow into: authentication, multi-user, database, cloud, leaderboards
— storage already hides behind a `SessionStore` seam, and the frontend treats
the API as its only contract.
