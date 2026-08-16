# Week 9+ (Upcoming Roadmap) — Empirical Benchmarking, Concurrency Hardening, UI Controls & Production Deployment

> **One-line goal:** Transition from development to formal empirical validation by running a 50-prompt automated benchmark to quantify geometric and semantic pass rates, hardening API concurrency and rate limits, adding standard engineering camera presets and export tools, and containerizing the full stack for production deployment.

---

## 1. Status of Prior Carry-Over Items (Verified & Closed)

Before entering the final benchmarking and deployment phase, all outstanding architectural and verification items from Weeks 7 and 8 were formally closed and tested:

| Item | Resolution & Status | Evidence / Verification |
|---|---|---|
| **Chassis Recompute Numbers** | **Resolved.** Reconciled single-parameter length scaling (+5.3% length → +4.8% volume, width/thickness constant) vs. proportional 3-axis scaling (+36.2% volume). | Documented in [`week8.md`](file:///d:/Projects/Minor_project/docs/review/week8.md). |
| **Geometry Validation Enforcement** | **Resolved.** Wired `is_valid` into the retry loop in `main.py`. If `is_valid == False` (`body_count > 1` or non-manifold), `main.py` feeds topology errors into `LLMService.correct_code()`. | [`main.py`](file:///d:/Projects/Minor_project/backend/main.py#L130-L165) + [`test_geometry_validation.py`](file:///d:/Projects/Minor_project/backend/test_geometry_validation.py) (2 passed). |
| **PARAMS Preservation on Modify** | **Resolved.** Tested parameter superset invariant during structural modifications. | [`test_modify_params.py`](file:///d:/Projects/Minor_project/backend/test_modify_params.py) (1 passed). |
| **Script Version Persistence** | **Resolved.** File-based persistence in `MODELS_DIR / f"{script_id}.py"` for each version (`_v1`, `_v2`), retained until the 24-hour cleanup cycle. | [`services/cad_runner.py`](file:///d:/Projects/Minor_project/backend/services/cad_runner.py#L398). |
| **Event Loop Blocking Unblock** | **Resolved.** All synchronous LLM SDK network calls wrapped in `asyncio.to_thread`. | Documented with root-cause analysis in [`week8.md`](file:///d:/Projects/Minor_project/docs/review/week8.md). |

---

## 2. Prioritized Roadmap for Weeks 9–14

```
┌────────────────────────────────────────────────────────────────────────┐
│                        UPCOMING EXECUTION PHASES                       │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE 1 (Week 9):   Automated 50-Prompt Benchmark (benchmark_eval.py)  │
│                     • Two-tier scoring: Geometric Validity + Semantics │
│                     • Quantifies first-pass %, retry %, latency stats  │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE 2 (Week 10):  Concurrency Hardening & Rate Limiting              │
│                     • slowapi rate limiter (10 req/min per IP)         │
│                     • asyncio.Semaphore for CAD subprocess concurrency │
│                     • Secrets management for cloud deployment          │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE 3 (Week 11):  3D Engineering Controls & Export Center            │
│                     • Standard camera presets (Top, Front, Side, Iso)  │
│                     • Multi-format Export Center (STL, STEP, Python)   │
│                     • Simple Metallic / Matte PBR shader toggle        │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE 4 (Week 12):  Docker Containerization & Cloud Deployment         │
│                     • Debian-slim Dockerfile with OpenCASCADE binaries │
│                     • Backend deployment (Render) + Frontend (Vercel)  │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE 5 (W13–14):   Final Technical Report & Defense Presentation      │
│                     • Compiling benchmark tables, charts & telemetry   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Phase Breakdown

### Phase 1 (Week 9): 50-Prompt Automated Empirical Benchmark (`backend/benchmark_eval.py`)

To replace all informal development estimates (~80–90%) with rigorous, reproducible data for the final project report, we will execute a 50-prompt automated benchmark across 5 mechanical categories (Brackets, Enclosures, Rotational Parts, Fasteners, Robotics Hardware).

#### Defined Two-Tier Evaluation Criteria:
1. **Tier 1 — Geometric Topology Validity (Binary Pass/Fail via OpenCASCADE + Trimesh):**
   - `is_watertight == True` (Manifold 2-surface with no open boundaries).
   - `body_count == 1` (Single monolithic fused solid; zero floating islands).
   - `volume > 0` (Positive non-zero volume; outward-facing normal orientation).
   - `min_extent >= 0.1 mm` (No degenerate zero-thickness faces).
2. **Tier 2 — Parametric & Semantic Completeness (Schema Inspection):**
   - `len(parameters) >= 1` with valid ranges (`min <= default <= max`, `step > 0`).
   - Discrete integer parameters cast to `int` in range loops.
   - Script adheres to 15-rule structure and exports to `OUTPUT_STL` and `OUTPUT_STEP`.

#### Telemetry Captured & Output Artifacts:
- **First-Pass Success Rate (%)**: Fraction of prompts generating valid geometry on attempt 0.
- **Self-Correction Recovery Rate (%)**: Fraction of initially failing scripts repaired within 3 attempts.
- **Total System Pass Rate (%)**: Combined first-pass + repaired success rate.
- **Model Fallback Distribution**: Breakdown of requests served by Gemini 2.5 Flash vs 3.7 Flash vs Flash Latest vs Groq.
- **Latency Distribution**: Mean, median ($p50$), and 95th percentile ($p95$) generation time.

---

### Phase 2 (Week 10): Concurrency Hardening & Rate Limiting

To prepare the API for public staging and live multi-user evaluations without cost exposure:

- **Per-IP Rate Limiting:** Integrate `slowapi` middleware onto `/api/generate` and `/api/modify` (e.g. 10 requests per minute per client IP) to protect paid LLM quota.
- **Process Concurrency Cap:** Implement module-level `asyncio.Semaphore(max(1, (os.cpu_count() or 2) - 1))` inside `CADRunner.execute_script_async()` to prevent CPU starvation when multiple CAD subprocesses execute simultaneously.
- **Production Secrets Management:** Ensure `GEMINI_API_KEY` and `GROQ_API_KEY` are injected via platform environment variables (Render/Fargate secrets) with zero hardcoded defaults in code or Docker images.

---

### Phase 3 (Week 11): 3D Engineering Controls & Export Center

- **Standard Camera Views (`Viewer3D.jsx`):**
  Add top-right floating viewport toolbar with instant camera angle snaps:
  - **Top View:** `camera.position.set(center.x, center.y + d, center.z)`
  - **Front View:** `camera.position.set(center.x, center.y, center.z + d)`
  - **Side View:** `camera.position.set(center.x + d, center.y, center.z)`
  - **Isometric View:** `camera.position.set(center.x + d, center.y + d, center.z + d)`
  - **Reset View:** Returns to default FOV bounding sphere fit.
- **Multi-Format Export Center:**
  Modal/dropdown to download manufacturing assets:
  - `.stl` (Tessellated triangular mesh for 3D printing / slicers).
  - `.step` (ISO 10303 analytical solid for SolidWorks/Fusion 360/CAM).
  - `.py` (Raw standalone `build123d` Python script).
- **Simplified Material Mode Toggle:**
  A clean UI toggle between **Engineering Metallic Blue** (`metalness=0.4, roughness=0.25`) and **Matte Technical White** (`metalness=0.05, roughness=0.6`), avoiding the complexity and overhead of external texture maps.

---

### Phase 4 (Week 12): Docker Containerization & Deployment

- **Multi-Stage Dockerfile:**
  ```dockerfile
  FROM python:3.12-slim
  RUN apt-get update && apt-get install -y --no-install-recommends \
      libgl1-mesa-glx libglib2.0-0 \
      && rm -rf /var/lib/apt/lists/*
  WORKDIR /app
  COPY backend/requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY backend/ .
  COPY frontend/dist/ /app/static/frontend/
  EXPOSE 8000
  CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```
- **Deployment Strategy:** Container deployed on Render Web Service (persistent Linux container with 2GB+ RAM for OpenCASCADE), with frontend served via Vite static build or Vercel edge CDN.

---

### Phase 5 (Weeks 13–14): Final Technical Report & Defense Prep

- Consolidate all 14-week logs, benchmark data tables, latency histograms, and architectural diagrams into the final Minor Project thesis document.

---

## 4. Explicit Scope Reductions & Deferrals

| Proposed Feature | Decision | Engineering Justification |
|---|---|---|
| **Multi-Texture PBR Materials (Carbon Fiber / Brushed Aluminum)** | **Deprioritized / Simplified** | Replaced with a simple metallic/matte shader toggle. Texture maps add asset loading overhead without improving the core NL-to-CAD contribution. |
| **Dual-Tolerance Dynamic Tessellation** | **Sequenced After Profiling** | `/api/recompute` currently executes in 150–400ms. Dual-tolerance will only be built if profiling reveals slider lag on complex geometries. |
| **DXF 2D Profile Export** | **Deferred** | Most parts in the corpus are true 3D solids (chassis, brackets, enclosures). DXF is only meaningful for planar sheet metal parts. |
| **WebAssembly (Wasm) Porting** | **Documented as Future Work** | Compiling OpenCASCADE C++ to Wasm is beyond the scope of a semester project; containerized backend is the correct architecture. |

---

## 5. Exit Criteria for the Completion Phase

| Phase | Milestone Metric | Success Condition |
|---|---|---|
| **Week 9** | 50-Prompt Automated Benchmark | Comprehensive telemetry report generated; Total Success Rate $\ge 85\%$ |
| **Week 10** | Rate Limiting & Concurrency | 5 concurrent requests handled smoothly without deadlock or quota breach |
| **Week 11** | Engineering Viewport Tools | Camera view buttons and multi-format download center working in UI |
| **Week 12** | Production Cloud Deployment | Live containerized service running on Render with passing health checks |
| **Week 14** | Final Report Submission | Complete data-backed technical thesis with verified metrics |
