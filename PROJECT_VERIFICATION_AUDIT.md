# Independent Technical Verification Audit Report

**Target Document:** `PROJECT_TECHNICAL_DOSSIER.md`  
**Repository:** `AI Parametric CAD Workbench`  
**Current Branch:** `main`  
**Commit Hash:** `a83dca44d30f4a1b8c3bef9e5a15d56827e7b426`  
**Date of Audit:** November 22, 2026  
**Evaluation Scope:** Factual cross-examination of technical claims, architecture descriptions, API contracts, test counts, benchmark metrics, and security mechanisms against the active project repository.

---

## 1. Executive Summary

This independent technical audit was conducted to verify every technical assertion, architectural representation, performance metric, and security guarantee presented in `PROJECT_TECHNICAL_DOSSIER.md`. The codebase was inspected at the source level, cross-referenced with configuration files, dependency manifests, and automated CI workflows, and evaluated via runtime test execution.

### Key Audit Findings:
1. **Core Pipeline & Features:** The core claims regarding the programmatic CAD generation pipeline, OpenCASCADE `build123d` integration, multimodal sketch parsing, fast parametric recomputation, React Three Fiber 3D viewport, and PostgreSQL/SQLite database schemas are **factually verified in the active codebase**.
2. **Test Count Discrepancies Reconciled:** The repository contains documented drift in test counts:
   - `README.md` reports **79 tests** [OUTDATED].
   - `AGENTS.md` reports **80 tests across 14 files** [OUTDATED].
   - `.github/workflows/ci.yml` runs **50 tests across 8 files** [VERIFIED BY EXECUTION in CI configuration].
   - The active local test suite collects **89 tests across 15 files**, with **88 passed and 1 skipped by design** in 188.72 seconds [VERIFIED BY EXECUTION].
3. **Benchmark Latency Correction:** The dossier claimed a $P_{50}$ generation latency of $14.2\text{ s}$. Analysis of the raw data in `backend/benchmark_results.json` reveals that $14.2\text{ s}$ was the latency of a single prompt (`l_bracket`). The **actual mathematical median ($P_{50}$) across all 20 prompts is $17.25\text{ s}$ ($17,250\text{ ms}$)**, and the mean latency is $17.14\text{ s}$ ($17,140\text{ ms}$) [INCORRECT IN DOSSIER].
4. **Security Claim Calibration:** The dossier previously characterized AST validation as a mechanism that "eliminates Remote Code Execution (RCE) vulnerabilities". In Python, static AST analysis is a heuristic defense-in-depth filter, not a complete kernel-level or hypervisor-level security sandbox. Subprocess execution with stripped environments and timeouts mitigates attack impact, but AST validation alone does not formally guarantee complete immunity [INCORRECT OVERCLAIM].
5. **Recomputation Benchmark Evidence:** The claimed $164\text{ ms}$ slider recomputation latency is consistent with local kernel execution characteristics, but exists without a saved automated benchmark log in the repository, unlike the 20-prompt generation benchmark [UNVERIFIED BY LOG].

---

## 2. Granular List of Verified Features

The following features were evaluated against source files and live runtime execution:

### 2.1 Backend & CAD Architecture
- **OpenCASCADE `build123d` Kernel Execution:**
  - *Status:* `VERIFIED IN SOURCE` & `VERIFIED BY EXECUTION`
  - *Evidence:* [backend/services/cad_runner.py](file:///d:/Projects/Minor_project/backend/services/cad_runner.py#L304-L365), [backend/services/cad_runner.py](file:///d:/Projects/Minor_project/backend/services/cad_runner.py#L480-L540).
  - *Details:* Subprocess wrapper dynamically injects `OUTPUT_STL` and `OUTPUT_STEP` absolute paths and invokes Python in a thread pool. Tested via `test_pipeline.py` and `test_geometry_validation.py`.
- **Subprocess Isolation & Concurrency Control:**
  - *Status:* `VERIFIED IN SOURCE`
  - *Evidence:* [backend/services/cad_runner.py](file:///d:/Projects/Minor_project/backend/services/cad_runner.py#L128), [backend/services/cad_runner.py](file:///d:/Projects/Minor_project/backend/services/cad_runner.py#L480-L514).
  - *Details:* `CAD_EXECUTION_SEMAPHORE = asyncio.Semaphore(CAD_MAX_CONCURRENT_EXECUTIONS)` restricts concurrent CAD compiles to 2. Environment dictionary is explicitly stripped of credentials, setting `PYTHONNOUSERSITE="1"` and `PYTHONPATH=""`.
- **Fast Preview Recomputation Tolerance:**
  - *Status:* `VERIFIED IN SOURCE`
  - *Evidence:* [backend/services/cad_runner.py](file:///d:/Projects/Minor_project/backend/services/cad_runner.py#L317-L327).
  - *Details:* When `fast_preview=True`, `build123d.export_stl` is patched at runtime to `tolerance=0.01` and `angular_tolerance=0.25`, reducing polygon generation time.
- **Mesh Topology & Watertight Manifold Validation:**
  - *Status:* `VERIFIED IN SOURCE` & `VERIFIED BY EXECUTION`
  - *Evidence:* [backend/services/cad_runner.py](file:///d:/Projects/Minor_project/backend/services/cad_runner.py#L566-L668).
  - *Details:* Uses `trimesh` to verify `is_watertight`, asserts positive volume ($V > 0$), and detects disjoint solid bodies via `trimesh.graph.connected_components`. Mode-aware logic handles `single_solid` vs `assembly`.
- **Multi-Tier LLM Orchestration:**
  - *Status:* `VERIFIED IN SOURCE`
  - *Evidence:* [backend/services/llm_service.py](file:///d:/Projects/Minor_project/backend/services/llm_service.py#L440-L498).
  - *Details:* Tier 1 invokes Google Gemini API via official `google-genai` SDK (`gemini-2.5-flash`, `gemini-3.5-flash-lite`, etc.); Tier 2 falls back to in-process Gemini Web client (`gemini_web_client.py`); Tier 3 falls back to Groq Cloud API (`llama-3.3-70b-versatile`).
- **Mechanical CAD Archetype Detection:**
  - *Status:* `VERIFIED IN SOURCE` & `VERIFIED BY EXECUTION`
  - *Evidence:* [backend/services/llm_service.py](file:///d:/Projects/Minor_project/backend/services/llm_service.py#L344-L412), [backend/test_universal_archetypes.py](file:///d:/Projects/Minor_project/backend/test_universal_archetypes.py#L22-L48).
  - *Details:* Regex detection matches prompts for 8 classes (shafts, enclosures, gears, piping, lofts, brackets, consumer/mugs, assemblies) and injects targeted geometric directives into system prompts.
- **Closed-Loop Automated Self-Correction:**
  - *Status:* `VERIFIED IN SOURCE` & `VERIFIED BY EXECUTION`
  - *Evidence:* [backend/main.py](file:///d:/Projects/Minor_project/backend/main.py#L447-L485), [backend/services/llm_service.py](file:///d:/Projects/Minor_project/backend/services/llm_service.py#L533-L554).
  - *Details:* Bounded at `MAX_RETRIES = 3`. Subprocess stderr or mesh topology warnings are injected into `CORRECTION_PROMPT_TEMPLATE` for iterative code repair.
- **Local Semantic RAG Engine:**
  - *Status:* `VERIFIED IN SOURCE` & `VERIFIED BY EXECUTION`
  - *Evidence:* [backend/services/rag_service.py](file:///d:/Projects/Minor_project/backend/services/rag_service.py#L35-L126).
  - *Details:* Local persistent ChromaDB collection holding 121 domain blueprints across 6 seed files embedded via `sentence-transformers` (`all-MiniLM-L6-v2`, 384 dimensions).
- **Multimodal Geometric Chain-of-Thought Sketch Parsing:**
  - *Status:* `VERIFIED IN SOURCE` & `VERIFIED BY EXECUTION`
  - *Evidence:* [backend/services/vision_service.py](file:///d:/Projects/Minor_project/backend/services/vision_service.py#L423-L520), [backend/test_sketch_endpoint.py](file:///d:/Projects/Minor_project/backend/test_sketch_endpoint.py#L1-L184).
  - *Details:* Enforces 7-step structured JSON reasoning (`SketchVisionAnalysis`) extracting dimensions, extrusion axes, and manufacturing curve rules before solid synthesis. Tested across 8 dedicated test cases.
- **Export Pipelines (STL, STEP, OBJ, GLB, ZIP):**
  - *Status:* `VERIFIED IN SOURCE` & `VERIFIED BY EXECUTION`
  - *Evidence:* [backend/services/cad_runner.py](file:///d:/Projects/Minor_project/backend/services/cad_runner.py#L678-L694), [backend/main.py](file:///d:/Projects/Minor_project/backend/main.py#L1103-L1180).
  - *Details:* STEP and STL generated by OpenCASCADE kernel; OBJ and GLB exported via `trimesh` mesh and scene objects. ZIP endpoint compiles all formats into `{script_id}.zip`.

### 2.2 Database, Auth & API Layer
- **Async Relational Models & Migrations:**
  - *Status:* `VERIFIED IN SOURCE`
  - *Evidence:* [backend/database.py](file:///d:/Projects/Minor_project/backend/database.py#L22-L87), [backend/models/user.py](file:///d:/Projects/Minor_project/backend/models/user.py#L1-L46), [backend/models/project.py](file:///d:/Projects/Minor_project/backend/models/project.py#L1-L110), [backend/alembic/versions/dd865e7861b0_initial_schema.py](file:///d:/Projects/Minor_project/backend/alembic/versions/dd865e7861b0_initial_schema.py).
  - *Details:* SQLAlchemy 2.0 async engine with SQLite WAL pragmas (`busy_timeout=5000`, `synchronous=NORMAL`). Models: `User`, `Project`, `Generation`, `Version`. Alembic migration environment active.
- **Authentication & Token Rotation:**
  - *Status:* `VERIFIED IN SOURCE` & `VERIFIED BY EXECUTION`
  - *Evidence:* [backend/routes/auth.py](file:///d:/Projects/Minor_project/backend/routes/auth.py#L98-L215), [backend/services/auth_service.py](file:///d:/Projects/Minor_project/backend/services/auth_service.py#L95-L165).
  - *Details:* BCrypt password hashing with 72-byte truncation guard. JWT access tokens (15-min expiry) and refresh tokens (7-day expiry) with version-based rotation (`refresh_token_version`). Tested in `test_auth_projects.py`.
- **Sliding-Window Rate Limiting & Daily Quota:**
  - *Status:* `VERIFIED IN SOURCE` & `VERIFIED BY EXECUTION`
  - *Evidence:* [backend/main.py](file:///d:/Projects/Minor_project/backend/main.py#L84-L126), [backend/services/auth_service.py](file:///d:/Projects/Minor_project/backend/services/auth_service.py#L41-L93).
  - *Details:* In-memory sliding window enforcing 10 req/min for generate and modify, 40 req/min for recompute. Database-backed 50 generation/day quota for free-tier users. Tested in `test_quota.py`.
- **Public Community Gallery & Forking Engine:**
  - *Status:* `VERIFIED IN SOURCE`
  - *Evidence:* [backend/routes/gallery.py](file:///d:/Projects/Minor_project/backend/routes/gallery.py#L115-L422).
  - *Details:* Browse, tag filter, and search public designs. Atomic like increments (`Generation.like_count + 1`). Forking copies artifact files or regenerates geometry on demand to prevent shared state.

### 2.3 Frontend & 3D WebGL Interface
- **Three.js WebGL CAD Viewport (`Viewer3D.jsx`):**
  - *Status:* `VERIFIED IN SOURCE`
  - *Evidence:* [frontend/src/components/Viewer3D.jsx](file:///d:/Projects/Minor_project/frontend/src/components/Viewer3D.jsx#L124-L238).
  - *Details:* React Three Fiber scene with `STLLoader`, `THREE.EdgesGeometry` at $24^\circ$ threshold, `GizmoViewcube`, `GizmoViewport`, live section cut plane ($Y=0$), and 3D bounding dimension tags.
- **CAD Workbench Reducer & State Persistence:**
  - *Status:* `VERIFIED IN SOURCE`
  - *Evidence:* [frontend/src/hooks/useCADWorkbench.js](file:///d:/Projects/Minor_project/frontend/src/hooks/useCADWorkbench.js#L1-L377).
  - *Details:* Central state machine (`cadWorkbenchReducer`) managing model parameters, snapshots (`modelHistory`), stream progress, and local storage synchronization (`cad_last_model`, `STORAGE_VERSION = 1`).
- **Debounced Slider Dispatch & Race Protection:**
  - *Status:* `VERIFIED IN SOURCE`
  - *Evidence:* [frontend/src/App.jsx](file:///d:/Projects/Minor_project/frontend/src/App.jsx#L582-L612).
  - *Details:* 120ms debounce timer paired with `recomputeSequenceRef` to drop out-of-order asynchronous recomputation responses.

---

## 3. Incorrect and Outdated Claims

The audit identified specific discrepancies between claims in `PROJECT_TECHNICAL_DOSSIER.md` (or repo docs) and the actual implementation:

| Item | Claim in Dossier / Docs | Actual Code / Execution Reality | Status | Recommended Correction |
|---|---|---|---|---|
| **P50 Generation Latency** | $P_{50} = 14.2\text{ s}$ (`Table 10.1`) | `benchmark_results.json` shows median ($P_{50}$) is **$17.25\text{ s}$**; mean is **$17.14\text{ s}$**. $14.2\text{ s}$ was only prompt #4 (`l_bracket`). | `INCORRECT` | Update dossier to report exact median of $17.25\text{ s}$ ($17,250\text{ ms}$) and mean of $17.14\text{ s}$. |
| **README Test Count** | `79 tests, ~100 seconds` (`README.md:84`) | Active test suite contains **89 tests across 15 files**. | `OUTDATED` | Update `README.md` to state 89 tests across 15 files. |
| **AGENTS.md Test Count** | `80 tests / 14 files` (`AGENTS.md:20, 44`) | Active test suite contains **89 tests across 15 files** (added `test_sketch_endpoint.py` and additional AST tests). | `OUTDATED` | Update `AGENTS.md` test count reference to 89 tests / 15 files. |
| **AST Security Guarantee** | "Eliminate Remote Code Execution (RCE) vulnerabilities" (`Dossier Section 2.6`) | AST analysis is a static lexical filter. It blocks known AST nodes and attributes, but does not provide container/kernel-level isolation. | `INCORRECT OVERCLAIM` | Rephrase to: "Mitigates arbitrary code execution through static AST pattern matching and restricted subprocess environments." |
| **P50 Recompute Latency** | Measured value: $164\text{ ms}$ marked `[VERIFIED]` (`Table 10.1`) | No automated recomputation benchmark output exists in the repo; $164\text{ ms}$ is from manual observation. | `UNVERIFIED BY LOG` | Mark as "Empirically observed in local development (<200ms target); automated benchmark suite not logged." |
| **Material Presets Count** | Dossier initially listed 6 presets with informal names | `constants/materials.js` defines exactly 5 PBR presets: Standard Titanium, Machined Aluminum, Anodized Blue, Tooling Yellow, Cast Iron Slate. | `RESOLVED` | Dossier was corrected during prior turn; verified against `materials.js`. |
| **STLLoader Source** | Attributed exclusively to `three-stdlib` (`Table 3`) | `Viewer3D.jsx:25` imports directly from `three/examples/jsm/loaders/STLLoader.js`. | `RESOLVED` | Dossier was corrected during prior turn; verified against `Viewer3D.jsx`. |

---

## 4. Test Count Reconciliation

There has been confusion across project documentation regarding test counts. The exact breakdown is resolved below:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      TEST SUITE RECONCILIATION                         │
├──────────────────────────┬──────────────┬───────────────┬──────────────┤
│ Context                  │ Test Files   │ Total Tests   │ Passed / Skip│
├──────────────────────────┼──────────────┼───────────────┼──────────────┤
│ README.md (Legacy doc)   │ Unspecified  │ 79            │ Untracked    │
│ AGENTS.md (Mid-project)  │ 14           │ 80            │ Untracked    │
│ CI Pipeline (ci.yml)     │ 8            │ 50            │ 49 / 1       │
│ Full Local Test Runner   │ 15           │ 89            │ 88 / 1       │
└──────────────────────────┴──────────────┴───────────────┴──────────────┘
```

### Detailed File-by-File Test Inventory (Verified via `pytest --collect-only`):

| # | Test File | Test Count | Run in CI? | Verified Status | Scenarios Covered |
|---|---|---|---|---|---|
| 1 | `test_schemas.py` | 12 | **Yes** | `VERIFIED BY EXECUTION` | Parameter bounds, integer checks, prompt lengths, payload schema |
| 2 | `test_ast_security.py` | 15 | **Yes** | `VERIFIED BY EXECUTION` | Import whitelist, blocked builtins, dunder access, lambda exfil |
| 3 | `test_llm_parser.py` | 4 | **Yes** | `VERIFIED BY EXECUTION` | JSON fences, raw newlines, regex fallback, AST validation |
| 4 | `test_geometry_validation.py` | 4 | **Yes** | `VERIFIED BY EXECUTION` | Disconnected bodies, assembly mode, monolithic solid, missing STEP |
| 5 | `test_recompute_validation.py`| 3 | **Yes** | `VERIFIED BY EXECUTION` | Invalid mesh rejection, unique artifact IDs, rate limit headers |
| 6 | `test_auth_projects.py` | 5 | **Yes** | `VERIFIED BY EXECUTION` | BCrypt hashing, JWT encode/decode, project CRUD, permission gates |
| 7 | `test_universal_archetypes.py`| 6 | **Yes** | `VERIFIED BY EXECUTION` | 5 passed, 1 skipped (live LLM benchmark skipped by design) |
| 8 | `test_pipeline.py` | 1 | **Yes** | `VERIFIED BY EXECUTION` | End-to-end async pipeline execution |
| **CI Subtotal** | **8 files** | **50 tests** | | **49 passed, 1 skipped** |
| 9 | `test_api.py` | 5 | Local Only | `VERIFIED BY EXECUTION` | Admin token checks, production enforcement, async routes |
| 10| `test_gallery_and_formats.py`| 1 | Local Only | `VERIFIED BY EXECUTION` | Gallery browsing, tag filtering, metrics endpoint payload |
| 11| `test_gemini_web_client.py` | 7 | Local Only | `VERIFIED BY EXECUTION` | Model specs, privacy flags, SAPISID hashing, stream response |
| 12| `test_modify_params.py` | 5 | Local Only | `VERIFIED BY EXECUTION` | Modify request validation, prompt bounds, version ID safety |
| 13| `test_pii_scrub.py` | 3 | Local Only | `VERIFIED BY EXECUTION` | Email redaction, phone number redaction, token redaction |
| 14| `test_quota.py` | 10 | Local Only | `VERIFIED BY EXECUTION` | UTC reset, 429 exhaustion, guest bypass, ZIP export, gating |
| 15| `test_sketch_endpoint.py` | 8 | Local Only | `VERIFIED BY EXECUTION` | Multipart image validation, MIME checks, happy path PNG/JPEG |
| **Full Total** | **15 files** | **89 tests** | | **88 passed, 1 skipped** |

*Execution Evidence:* `cd backend && .\venv\Scripts\python.exe -m pytest -q --tb=short` executed in 188.72s.

---

## 5. Benchmark Verification & Analysis

The benchmark evaluation script (`backend/benchmark_eval.py`) and recorded output (`backend/benchmark_results.json`) were examined:

### 5.1 Benchmark Setup & Methodology
- **Automated Script:** `benchmark_eval.py` sequentially posts 20 standard mechanical prompts to `POST /api/generate` with a 180-second timeout.
- **Model Used:** `gemini-2.5-flash` via official Gemini API.
- **Execution Date:** Recorded at `2026-09-18T12:00:00Z`.

### 5.2 Recorded Metrics Verification

```
Total Prompts: 20
├── Successful Generations: 18  (90.0%)
│   ├── First-Pass Success: 16  (80.0%)
│   └── Recovered via Self-Correction: 2  (10.0%)
└── Failed Generations: 2  (10.0%)
    ├── #19 chamfered_box: Chamfer face overlap on corner vertices
    └── #20 sphere_pedestal: Multiple disjoint solids detected
```

- **First-Pass Success Rate:** $16/20 = 80.0\%$ [`VERIFIED IN SOURCE` via JSON].
- **Overall Success Rate:** $18/20 = 90.0\%$ [`VERIFIED IN SOURCE` via JSON].
- **Self-Correction Recovery Rate:** Out of 4 initial non-first-pass attempts, 2 recovered successfully within 3 retry attempts $\to 2/4 = 50.0\%$ [`VERIFIED IN SOURCE` via JSON].
- **Latency Distribution Analysis:**
  - *Minimum Latency:* $11,200\text{ ms}$ (`box_basic`)
  - *Maximum Latency:* $31,200\text{ ms}$ (`sphere_pedestal`, failed after 3 retries)
  - *Mathematical Mean:* $17,140\text{ ms}$ ($17.14\text{ s}$)
  - *Mathematical Median ($P_{50}$):* Sorted 10th and 11th items are $16,900\text{ ms}$ and $17,600\text{ ms}$ $\to \mathbf{17,250\text{ ms}}$ ($\mathbf{17.25\text{ s}}$).
  - *Dossier Claim ($14.2\text{ s}$):* Reflected only `l_bracket`, not the distribution median [`INCORRECT IN DOSSIER`].

---

## 6. Security Claim Verification

The project dossier claims rigorous security sandboxing. The actual code was audited to verify the boundaries and limitations of this security architecture:

### 6.1 Implemented Defenses (`VERIFIED IN SOURCE`)
1. **Script ID Validation:**
   - Enforced by `is_safe_script_id()`: `^[A-Za-z0-9_-]{1,100}$` in [backend/services/cad_runner.py](file:///d:/Projects/Minor_project/backend/services/cad_runner.py#L90-L94).
   - Rejects directory traversal payloads (e.g., `../../etc/passwd`) before touching the filesystem or invoking CAD execution.
2. **Static AST Lexical Filtering:**
   - Enforced by `validate_script_safety()` in [backend/services/cad_runner.py](file:///d:/Projects/Minor_project/backend/services/cad_runner.py#L168-L242).
   - Rejects forbidden syntax nodes: `Lambda`, `Yield`, `YieldFrom`, `Await`, `Global`, `Nonlocal`.
   - Whitelists only 11 safe modules (`build123d`, `math`, `typing`, `types`, `collections`, `itertools`, `functools`, `enum`, `dataclasses`, `abc`, `operator`).
   - Blocks dangerous builtins: `open`, `eval`, `exec`, `compile`, `__import__`, `input`, `globals`, `locals`, `getattr`, `setattr`, `delattr`, `breakpoint`.
   - Rejects attribute access starting with `__` or referencing reflection dunders (`__subclasses__`, `__globals__`, `__code__`, `__mro__`).
3. **Subprocess Environment Isolation:**
   - Subprocess runs in a separate OS process with a stripped environment (`isolated_env`) containing only standard OS system roots and PATH, with `PYTHONNOUSERSITE="1"` and `PYTHONPATH=""`.
   - Bounded by a 60-second timeout kill switch.
4. **PII Redaction Pipeline:**
   - Enforced by `scrub_pii()` in [backend/services/llm_service.py](file:///d:/Projects/Minor_project/backend/services/llm_service.py#L38-L63).
   - Regex-redacts emails, phone numbers, AWS keys, GitHub tokens, and Bearer headers before dispatching prompts to LLM APIs.

### 6.2 Technical Limitations & Security Vulnerabilities (`REALITY CHECK`)
- **AST is Not a Complete Sandbox:**
  In CPython, static AST analysis cannot anticipate every dynamic code execution path, memory corruption exploit, or C-extension side channel. While `validate_script_safety` blocks common reflection and evasion techniques, treating it as an impenetrable sandbox that "eliminates RCE" is an academic overclaim.
- **Resource Exhaustion Attacks (DoS):**
  A user script passing valid `build123d` syntax could perform millions of nested boolean operations or complex fillets that monopolize 100% of the host CPU and consume gigabytes of RAM until the 60-second subprocess timeout fires.
- **In-Memory Rate Limiting:**
  `SimpleRateLimiter` is process-local (`defaultdict(list)`). In a multi-worker production deployment behind Nginx, clients can bypass limits by hitting different worker processes.
- **Storage Race Conditions:**
  `ArtifactCleanupManager` deletes files based on `mtime`. A generation request in flight could have its temporary script touched or deleted if TTL is set too aggressively.

---

## 7. Technology and Dependency Verification

Versions in `PROJECT_TECHNICAL_DOSSIER.md` were cross-checked with active project lockfiles and dependency manifests:

| Category | Technology | Claimed Version | Verified Manifest Version | Manifest File | Verification Status |
|---|---|---|---|---|---|
| Frontend Framework | React | `^19.2.8` | `"react": "^19.2.8"` | `frontend/package.json` | `VERIFIED IN SOURCE` |
| Frontend DOM | React-DOM | `^19.3.0` | `"react-dom": "^19.3.0"` | `frontend/package.json` | `VERIFIED IN SOURCE` |
| Build Tool | Vite | `^8.3.4` | `"vite": "^8.3.4"` | `frontend/package.json` | `VERIFIED IN SOURCE` |
| 3D WebGL Library | Three.js | `^0.186.1` | `"three": "^0.186.1"` | `frontend/package.json` | `VERIFIED IN SOURCE` |
| Declarative 3D | @react-three/fiber | `^9.8.2` | `"@react-three/fiber": "^9.8.2"`| `frontend/package.json` | `VERIFIED IN SOURCE` |
| 3D CAD Helpers | @react-three/drei | `^10.7.9` | `"@react-three/drei": "^10.7.9"` | `frontend/package.json` | `VERIFIED IN SOURCE` |
| Three.js Extensions | three-stdlib | `^2.36.1` | `"three-stdlib": "^2.36.1"` | `frontend/package.json` | `VERIFIED IN SOURCE` |
| HTTP Client | Axios | `^1.20.0` | `"axios": "^1.20.0"` | `frontend/package.json` | `VERIFIED IN SOURCE` |
| Syntax Highlighting | Prism.js | `^1.30.0` | `"prismjs": "^1.30.0"` | `frontend/package.json` | `VERIFIED IN SOURCE` |
| Frontend Linter | Oxlint | `^1.86.0` | `"oxlint": "^1.86.0"` | `frontend/package.json` | `VERIFIED IN SOURCE` |
| Backend Framework | FastAPI | `>=0.141.1` | `fastapi>=0.141.1` | `backend/requirements.txt` | `VERIFIED IN SOURCE` |
| CAD Engine | build123d | `>=0.8.0` | `build123d>=0.8.0` | `backend/requirements.txt` | `VERIFIED IN SOURCE` |
| Mesh Processing | Trimesh | `>=5.1.0` | `trimesh>=5.1.0` | `backend/requirements.txt` | `VERIFIED IN SOURCE` |
| Vector Database | ChromaDB | `>=1.5.9` | `chromadb>=1.5.9` | `backend/requirements.txt` | `VERIFIED IN SOURCE` |
| Embeddings | Sentence-Transformers | `>=3.0.0` | `sentence-transformers>=3.0.0` | `backend/requirements.txt` | `VERIFIED IN SOURCE` |
| Database ORM | SQLAlchemy | `>=2.0.0` | `sqlalchemy[asyncio]>=2.0.0` | `backend/requirements.txt` | `VERIFIED IN SOURCE` |
| Migrations | Alembic | `>=1.13.0` | `alembic>=1.13.0` | `backend/requirements.txt` | `VERIFIED IN SOURCE` |
| Cloud LLM SDK | Google GenAI SDK | `>=2.25.0` | `google-genai>=2.25.0` | `backend/requirements.txt` | `VERIFIED IN SOURCE` |
| Fallback LLM SDK | Groq Python SDK | `>=1.0.0` | `groq>=1.0.0` | `backend/requirements.txt` | `VERIFIED IN SOURCE` |

---

## 8. Missing Evidence

The following claims are present in documentation or user interface representations but lack recorded empirical evidence in the repository:

1. **Empirical Slider Recompute Latency Log:**
   - *Claim:* $P_{50} = 164\text{ ms}$ recomputation latency.
   - *Audit Finding:* While direct parameter injection bypasses LLM inference and local execution confirms sub-second recomputations, there is no automated benchmark script or JSON log file recording a formal distribution of 50 or 100 slider adjustments.
   - *Status:* `UNVERIFIED BY LOG`.
2. **Physical 3D Print Slicing Verification:**
   - *Claim:* Generates 3D-printable, watertight STL files ready for Cura or PrusaSlicer.
   - *Audit Finding:* Mesh watertightness is verified computationally via `trimesh.is_watertight`, but no physical prints or slicer g-code output logs are preserved in the repository.
   - *Status:* `NEEDS TEAM CONFIRMATION`.
3. **Multi-Browser WebGL Profiling:**
   - *Claim:* WebGL viewer verified across Chrome, Firefox, and Safari.
   - *Audit Finding:* No cross-browser automated Playwright test reports or GPU shader frame rate traces exist in the repository.
   - *Status:* `NEEDS TEAM CONFIRMATION`.

---

## 9. Questions Requiring Team Confirmation

The following academic and institutional details must be confirmed by the student project team before finalizing the JUET report:

1. **Student Team Member Details & Work Breakdown:**
   - Who implemented the backend AST sandbox and CAD runner?
   - Who implemented the React Three Fiber viewport and shader styles?
   - Who designed the database schema, JWT auth, and gallery routes?
   - Who conducted the benchmark evaluations?
2. **Academic Supervisor Details:**
   - Full name, academic title, and department of the project mentor/supervisor at JUET Guna.
3. **Physical Hardware Environment:**
   - What exact machine (CPU model, RAM capacity, GPU model, and OS version) was used to run the 188-second test suite and benchmark evaluations?
4. **Recomputation Benchmarking Protocol:**
   - Was the $164\text{ ms}$ recomputation metric recorded using Chrome DevTools Network Tab or an internal telemetry log?

---

## 10. Final List of Corrections for `PROJECT_TECHNICAL_DOSSIER.md`

To ensure 100% academic integrity and factual defensibility before university evaluation, the following modifications should be applied to `PROJECT_TECHNICAL_DOSSIER.md`:

1. **Correct Table 10.1 P50 Latency:**
   - *Current:* `P50 Generation Latency: 14.2 s`
   - *Corrected:* `P50 Generation Latency: 17.25 s (17,250 ms) | Mean Latency: 17.14 s (17,140 ms)`
2. **Clarify Recompute Benchmark Status in Table 10.1:**
   - *Current:* `P50 Recompute Latency: 164 ms [VERIFIED]`
   - *Corrected:* `P50 Recompute Latency: <200 ms target (164 ms empirically observed in manual telemetry; no automated benchmark log committed)`
3. **Calibrate Security Language in Section 2.6 and Section 11:**
   - *Current:* "Enforce strict AST-level process sandboxing to eliminate Remote Code Execution (RCE) vulnerabilities."
   - *Corrected:* "Enforce defense-in-depth security coupling static AST inspection (import whitelist, blocked builtins, dunder access prevention) with isolated subprocess execution, stripped environment variables, and bounded execution timeouts."
4. **Update Project Test Count References:**
   - Clarify that the active repository contains **89 collected test items across 15 files** (88 passed, 1 skipped by design), reconciling the legacy counts in `README.md` (79) and `AGENTS.md` (80) with CI (50 in 8 core files).
5. **Note Assembly Mode Constraints in Limitations:**
   - State clearly that while `design_mode='assembly'` supports multi-body solid geometry validation, dynamic mechanical kinematics (revolute joints, gear meshing, physics collision) are out of scope for the current implementation.

---
*End of Independent Verification Audit Report.*  
*Generated on November 22, 2026 for JUET B.Tech CSE Minor Project Evaluation.*
