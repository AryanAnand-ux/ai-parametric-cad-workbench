# AGENTS.md — AI Parametric CAD Workbench

Agent notes for this repo. `rules.md` (coding standards) and `CODEBASE_GUIDE.md` (file-by-file
architecture) are the sources of truth; this file holds the operational gotchas and commands that
would otherwise cost an agent a debugging session.

## Layout & entrypoints

- `backend/main.py` — FastAPI `app`. Routers from `backend/routes/{auth,projects,gallery}.py`;
  the pipeline endpoints (`/api/generate`, `/api/generate/stream`, `/api/recompute`, `/api/modify`,
  `/static/models/{filename}`, `/api/download/*`, `/api/admin/*`) live **in `main.py` itself** —
  that is the sanctioned exception to the "no routes in main.py" rule.
- `backend/config.py` — env + all paths, loaded via `python-dotenv` from `backend/.env` at import.
- `frontend/src/main.jsx` → `Router.jsx` → `App.jsx` (workbench) / `pages/Gallery.jsx` /
  `LandingPage.jsx`. Hash routing only: `#app`, `#gallery`, `#model=<generationId>`, `#embed=<generationId>`.
- Vite dev server proxies `/api` and `/static` to `localhost:8000`; `VITE_API_URL` overrides the
  base URL for production (nginx).

## Commands (run from the stated directory)

```powershell
# backend — always use the venv interpreter, plain `python` may be the wrong one
cd backend
.\venv\Scripts\python.exe -m pytest -q --tb=short          # 80 tests / 14 files, ~105s
.\venv\Scripts\python.exe -m pytest test_ast_security.py -v # single file
.\venv\Scripts\python.exe main.py                          # honours RELOAD env (default: no reload)
.\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000

# frontend
cd frontend
npm run dev        # Vite :5173
npm run build      # production bundle
npm run lint       # oxlint — currently 0 errors / 0 warnings; keep it there
```

- `backend/pytest.ini` sets `asyncio_mode = auto` and `testpaths = .` → run pytest **from
  `backend/`**, and do not add `@pytest.mark.asyncio` to new async tests.
- There is **no frontend test runner and no typecheck** (plain JSX, no TS). UI changes are verified
  by `npm run build` plus a manual dev-server check.
- Ad-hoc scripts that `import main` must be run with the repo's `backend` on the path
  (`$env:PYTHONPATH = "D:\Projects\Minor_project\backend"`).
- CI = `.github/workflows/ci.yml` ("CI — Full Stack Suite"): Python 3.11 + Node 22, runs on
  push/PR touching `backend/`, `frontend/`. **CI only runs 8 of the 14 test files** — gallery,
  quota, PII, gemini-web, modify and API-contract tests are local-only, so run the full suite
  before claiming green. `.github/dependabot.yml` opens weekly pip/npm/actions bumps.

## Gotchas that cost real time

1. **Temp/model files must stay outside `backend/`.** `TEMP_DIR = <repo>/scratch/temp`,
   `MODELS_DIR = .../models`. Generated `.py`/`.stl` inside the backend tree make uvicorn's
   WatchFiles reloader restart mid-request → 500s. `scratch/` is gitignored.
2. **DB rows outlive their artifacts.** TTL cleanup deletes STL/STEP files while generations and
   gallery rows still reference them. `GET /static/models/{filename}` regenerates on demand from
   the stored `python_code`, so a missing file is often expected. But a *fork* must never point at
   the original's files — `routes/gallery.py` copies artifacts and regenerates geometry when they
   are gone.
3. **Script IDs are filenames and security boundaries.** `is_safe_script_id()`
   (`^[A-Za-z0-9_-]{1,100}$`) gates both CAD execution and artifact serving. `.py` artifacts
   require `X-Admin-Token`; path traversal and other suffixes 404. Never widen either check.
4. **Generation access is owner-only.** `GET /api/generations/{id}` will not load another user's
   gallery model — fork, then deep-link the returned `fork_id` (a **generation id**, not
   `script_id`). Downloads are the exception: missing-record, public, owner, or admin.
5. **AST validation before every CAD run is mandatory** (`services/cad_runner.py`), execution is
   an isolated subprocess with a 60s timeout and a global concurrency cap of 2
   (`CAD_MAX_CONCURRENT_EXECUTIONS`). LLM self-correction is capped at 3 retries; RAG retrieval is
   k=3. Do not raise these without load testing.
6. **Production gates are enforced at startup**: `ENVIRONMENT=production` refuses to boot without
   `ADMIN_TOKEN` and a non-default `JWT_SECRET_KEY`, and makes compute endpoints auth-required.
   The variable is `JWT_SECRET_KEY` (`README.md` still says `SECRET_KEY` — stale).
7. **`backend/.env` is auto-loaded on import**, so local keys silently apply to local test runs.
   Never commit it; use `backend/.env.example`. Note the example file is missing the
   `GEMINI_WEB2API_*` keys that `config.py` reads.
8. **The test suite is hermetic** — every LLM call is patched/monkeypatched and no test uses
   `skipif` (contrary to `rules.md` §3.7). Keep it that way: no network calls in tests.
9. **Fresh clones have no ChromaDB index** (`backend/rag_corpus/chroma_db/` is gitignored). Build
   it with `RAGService.build_index()`; otherwise `test_universal_archetypes.py` self-skips and RAG
   retrieval paths go untested. `RAG_BUILD_ON_STARTUP=true` adds 30–60s to boot.
10. **SQLite specifics**: `backend/database.py` sets WAL + `busy_timeout` pragmas. `pool_size` /
    `max_overflow` kwargs make SQLite raise `TypeError` — pool tuning must stay behind a
    non-SQLite check. Async sessions only; `create_all` is used instead of Alembic.
11. **Frontend state discipline**: all workbench model state lives in the `useCADWorkbench`
    reducer, auth in `useAuth`. Model state persists at `localStorage['cad_last_model']` (schema
    is version-guarded — keep it stable), token at `cad_token`. No router library, no Tailwind;
    all styling in `src/index.css` via CSS custom properties. All API calls go through
    `src/api.js`; components never call `fetch` directly. Asset URLs must be passed through
    `resolveAssetUrl()` so `VITE_API_URL` still applies.
12. **A second git worktree is checked out at `.kilo/worktrees/north-composer`** (untracked, same
    commit). Don't edit or commit files from there.
13. **`build123d` import costs 3–5s** in a fresh subprocess (OpenCASCADE/OCCT load), so the first
    CAD run of a session is always slow — that is not a hang. ChromaDB prints a telemetry
    opt-in warning on first run; set `ANONYMIZED_TELEMETRY=false` to silence it.
14. **SQLite is the default but not the ceiling.** `DATABASE_URL` can point at PostgreSQL
    (`asyncpg` is a dependency and `docker-compose.yml` ships a `postgres:16` service);
    concurrent writes queue under SQLite, so migration is the documented fix, not more pragmas.

## Working agreements

- Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`). `rules.md` §5
  wants a feature branch + PR; recent history also pushed straight to `main`. Keep CI green either
  way.
- **Mandatory live-update rule (`rules.md` §6.2): every code change updates the matching doc in the
  same commit** — API/schema → `prd.md` + `CODEBASE_GUIDE.md`; new service/module →
  `CODEBASE_GUIDE.md`; UI/styles → `design.md`; new convention → `rules.md`; bug fix or decision →
  `CHANGELOG.md`; finished task → `task.md`; env var → `backend/.env.example`; dependency →
  `CODEBASE_GUIDE.md`. Do not add ad-hoc markdown at the repo root — fold content into the existing
  docs.
- Test counts in the docs drift (79 vs 80). Trust `pytest --collect-only`, and fix the docs when
  you notice drift.
- The doc set is deliberately small: `README.md` (quickstart), `AGENTS.md` (this file), `rules.md`
  (standards), `CODEBASE_GUIDE.md` (architecture + file-by-file), `prd.md` (API contracts),
  `design.md` (UI system), `task.md` (backlog), `CHANGELOG.md` (history). `architecture.md` and
  `memory.md` were removed as duplicates — do not recreate them; extend the files above instead.
