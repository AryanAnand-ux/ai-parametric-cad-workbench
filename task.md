# Task Board
## AI Parametric CAD Workbench

**Last Updated:** September 27, 2026  
**Sprint:** Active Development  

> This file tracks current, upcoming, and completed development tasks.
> Update this file as work progresses. Mark items [x] when done.

---

### In Progress

- [x] Production deployment readiness & final polish

---

## Backlog — High Priority

### Backend
- [ ] Migrate SQLite → PostgreSQL for production deployments
- [ ] Add Alembic migrations (replace `create_all` on startup)
- [ ] Add streaming SSE progress for generation pipeline stages (RAG → LLM → Build → Export)
- [ ] Implement model thumbnail generation (render 3D screenshot server-side)
- [ ] `test_universal_archetypes.py` — run all 20 archetype prompts against live LLM in CI-optional mode

### Frontend
- [ ] Parameter sidebar: add parameter grouping by category (dimensions, features, tolerances)
- [x] Mobile responsive pass for workbench (sidebar collapse, toolbar reflow)
- [x] Model thumbnails in gallery (vector CAD blueprint archetypes with technical grid & badges)

### DevOps
- [x] Dockerfile healthcheck for the backend container (exists in `Dockerfile`)
- [ ] Set up Dependabot for Python + npm dependency updates

---

## Backlog — Medium Priority

- [ ] Dark mode toggle (CSS custom property swap)
- [ ] Code inspector: syntax highlighting for generated Python (Prism.js or similar)
- [ ] Export: add batch export (download all formats as ZIP)
- [x] Gallery: add pagination / infinite scroll
- [ ] Projects sidebar: drag-to-reorder projects
- [x] Add `CHANGELOG.md` to track version history

---

## Backlog — Low Priority / Ideas

- [ ] AI-suggested next prompts (LLM suggests variations based on current model)
- [ ] Split-view: prompt history timeline on the left
- [ ] 3D viewer: measurement tool (distance between two points)
- [ ] 3D viewer: section cut plane tool
- [x] Add build123d tutorial/docs link in onboarding tour
- [x] Telemetry HUD: add polygon count, material info

---

## Completed

- [x] Week 1-2: Project scaffolding, FastAPI setup, basic NL → CAD pipeline
- [x] Week 3: LLM service multi-tier fallback (Gemini → Groq), self-correction loop
- [x] Week 4: build123d CAD engine integration, CAD runner subprocess sandbox
- [x] Week 4: RAG corpus setup (ChromaDB + sentence-transformers)
- [x] Week 5: AST security validation, rate limiting, temp file cleanup
- [x] Week 6: SQLAlchemy database, user auth (JWT + bcrypt), projects CRUD
- [x] Week 7: React frontend — Viewer3D (React Three Fiber), workbench layout
- [x] Week 7: Parameter sliders, recompute endpoint, parameter editing
- [x] Week 8: Chat-to-modify panel, modification history
- [x] Week 8: Gallery page, share modal, public gallery backend
- [x] Week 8: Onboarding tour, auth modal (login/register)
- [x] Week 9+: Universal archetypes — 20 CAD archetypes, 121-doc RAG index
- [x] Navbar refactor — compact segmented controls, user dropdown, unified status indicator
- [x] Logo → home navigation — brand logo routes to landing page via `onGoHome` callback
- [x] CI/CD — 33/33 pytest tests passing, Vite production build verified
- [x] Documentation suite — all 6 core .md files created and kept in live sync
- [x] Keyboard shortcuts — G (Generate), R (Force Recompute), E (Export), ? (Tour), Z (Undo)
- [x] Tour persistence — localStorage caching of completion flag across sessions + user menu reset
- [x] Full-Stack CI/CD — GitHub Actions workflow runs 41 pytest tests + Vite frontend production build on push/PR
- [x] Rate limit headers — `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` on API responses + 429 detail
- [x] Gallery live search & discipline chips — debounced client-side search + extended tags filter
- [x] CI greenlet fix — `sqlalchemy[asyncio]` + explicit `greenlet` + `bcrypt` in requirements (8 straight CI failures fixed, suite green)
- [x] Pre-deploy security hardening — AST allowlist (dunder/alias/lambda blocks + 6 adversarial tests), prod-only auth gate on compute endpoints, download ownership checks, refresh-token rotation, login rate limits, PII scrubber (69 tests passing)
- [x] Share-link routes — `#model=`/`#embed=` now deep-link into workbench via `initialGenerationId`
- [x] SSE cancellation + state fixes — AbortController on generate, paramValuesRef via useEffect, undo deep-clone + persist, single tour key, sidebar refetch fix
- [x] Deploy config — DB on volumed path, TRUST_PROXY wiring, real benchmark gate, demo creds removed, SEO meta + nginx hardening (gzip/caching/security headers)
- [x] Round-2 hardening — RAG guards, SSE disconnect, version-record fields, LLM timeouts, tag escaping, DB indexes, atomic likes, pagination, sort/tag validation, bcrypt limit, telemetry caps, subprocess cwd, stderr scrub, security headers, 480px CSS, viewer code-split, health polling, alert→inline, escape-to-close
- [x] Round-3 product + a11y — daily quotas (50/day free), per-user rate keys, batch ZIP export, focus-trap system, gallery load-more, export-all button, dev-only logger, slider drafts, Dependabot
- [x] Round-4 stack — PyJWT swap (jose removed), Postgres-ready compose, Dockerfile 3.11, tour docs link, telemetry face chip, merged vite + plugin-react bumps
- [x] Round-5 dependency wave — merged actions/checkout+setup-node+setup-python v7, vite, plugin-react, three, fiber, react-dom; applied dotenv/shapely/trimesh-5/chromadb-1.5 manually (RAG verified on chroma 1.x), closed superseded PRs
- [x] Gallery→workspace handoff — fork banner deep-links `#model=<fork_id>`, deep links override cached models, fork regenerates missing geometry + self-contained artifacts, detail endpoint serves obj/glb URLs
- [x] Archetype geometry verification — robust single-solid build123d topology for V-Belt Pulley, Flanged Pipe Elbow, HVAC Transition Duct; all 8 community gallery models seeded and verified
- [x] Frontend runtime fix — added missing `useCallback` import in `OnboardingTour.jsx` preventing component crash on first visit
- [x] Doc consolidation — deleted `architecture.md` + `memory.md` as duplicates; doc set is now README, AGENTS, rules, CODEBASE_GUIDE, prd, design, task, CHANGELOG

---

## Notes

- Backend test suite: `cd backend && python -m pytest -v` (80 tests, ~98s)
- Frontend dev server: `cd frontend && npm run dev` (Vite, port 5173)
- Backend dev server: `cd backend && uvicorn main:app --reload --port 8000`
- RAG index rebuild: `python -c "from services.rag_service import RAGService; RAGService.build_index()"`
