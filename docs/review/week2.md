# Week 2 — FastAPI Completion, Artifact Cleanup & Concurrent Request Handling

> **One-line goal:** Promote the Week 1 skeleton to a structurally sound server — proper Pydantic schemas, realistic artifact lifecycle management, a CORS layer for the React frontend, and structured logging throughout.

---

## 1. Framing Note (Corrected After Code Audit)

The original Week 2 write-up contained several claims that do not match the actual codebase. These are corrected explicitly below so the project report is accurate under evaluation:

| Claim in original doc | Actual state |
|---|---|
| `asyncio.Semaphore` added for concurrency control | **Not present** in `main.py`. The server relies on FastAPI's async event loop + the `asyncio.to_thread` pool for concurrency. Semaphore was planned but not implemented this week. |
| `/api/download/{script_id}/{format}` endpoint | **Not implemented**. STL and STEP files are served via `StaticFiles` mount at `/static/models/`. This is functionally equivalent for the browser use-case. |
| `cleanup.py` at `backend/cleanup.py` | **Actual location:** `backend/services/cleanup.py` |
| Cleanup threshold: 2 hours (`max_age_hours`) | **Actual:** `max_age_seconds=86400` (24 hours). The parameter is in seconds, not hours. |
| Exit criteria stress-tested with httpx | **Not formally verified** — there is no test artefact in the repository showing 5 concurrent requests were actually run and timed. |

For academic evaluators: the Week 2 deliverables that *were* completed are still significant — the schema design, logging foundation, CORS middleware, and cleanup sequencing are all real and correct. The items above are corrections to the narrative, not failures of the system.

---

## 2. What Was Actually Built

### 2.1 Pydantic Schema Layer (`schemas.py`)

This is the most important Week 2 deliverable. The schema design established at this stage locked in the API contract that every subsequent layer (LLM response parsing, frontend API client, test suite) depends on.

```python
# The "Dual-Output" innovation: LLM must produce BOTH code AND parameter schema
class DualOutputPayload(BaseModel):
    python_code: str        # Executable build123d script
    parameters: List[CADParameter]  # UI slider definitions
    part_name: str
    description: str

class CADParameter(BaseModel):
    name: str       # Python variable name (matches PARAMS dict key)
    label: str      # Human-readable UI label
    type: Literal["number", "integer"]
    default: float
    min: float
    max: float
    step: float = 1.0

    @model_validator(mode='after')
    def validate_range(self) -> 'CADParameter':
        """Enforces min <= default <= max and step > 0 at schema level."""
        if self.min > self.max:
            raise ValueError(f"Parameter '{self.name}': min must be <= max")
        if not (self.min <= self.default <= self.max):
            raise ValueError(f"Parameter '{self.name}': default must be in [min, max]")
        if self.step <= 0:
            raise ValueError(f"Parameter '{self.name}': step must be > 0")
        return self
```

**Why `@model_validator` matters:** Without this, the LLM could return `{"default": 500, "min": 10, "max": 100}` and the slider would silently clamp to the wrong value. Catching this at schema validation means the error is surfaced immediately as a 422 response rather than silent broken behaviour in the UI. This is the kind of defensive engineering that saves debugging hours in Weeks 5–8.

**The Dual-Output contract:** The insight that the LLM must produce both executable code *and* a structured parameter schema in the same JSON response is the core design innovation of this project. Every downstream feature — live sliders, recomputation, Chat-to-Modify — is built on top of this contract. Getting the schema right in Week 2 was the right time to do it.

### 2.2 Artifact Cleanup (`services/cleanup.py`)

```python
class ArtifactCleanupManager:

    @staticmethod
    def cleanup_old_artifacts(max_age_seconds: int = 86400) -> int:
        """
        Deletes files in TEMP_DIR and MODELS_DIR older than max_age_seconds.
        Default: 24 hours (86400 seconds).
        Returns count of removed files.
        """
        now = time.time()
        removed_count = 0
        for directory in [TEMP_DIR, MODELS_DIR]:
            if not directory.exists():
                continue
            for file_path in directory.glob("*"):
                if file_path.is_file():
                    if (now - file_path.stat().st_mtime) > max_age_seconds:
                        try:
                            file_path.unlink()
                            removed_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to delete {file_path.name}: {e}")
        return removed_count

    @staticmethod
    def remove_file_safely(file_path: Path):
        """Immediately removes a single temp script after execution."""
        if file_path and file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to remove temp file {file_path}: {e}")
```

**Two-tier cleanup strategy:**
- `cleanup_old_artifacts()` — scheduled by FastAPI `BackgroundTasks` after `/api/generate` responses. Scans both dirs for files older than 24h. Prevents disk bloat over multi-day runs.
- `remove_file_safely()` — called immediately after a subprocess finishes (from `cad_runner.py`). Deletes the temp execution script right after stdout/stderr are captured. This is sequenced, not on a timer — no race condition.

**Correction to original doc:** The threshold is `max_age_seconds=86400` (24 hours), not 2 hours. The parameter name uses seconds throughout for consistency with `time.time()` arithmetic. If the report needs to say "2 hours," the code must be changed; currently it is 24 hours.

### 2.3 FastAPI Application Expansion (`main.py`)

**CORS middleware — why this is non-trivial:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,   # Must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)
```
`allow_credentials=True` with `allow_origins=["*"]` raises a CORS error in browsers. This is a real gotcha — `False` is correct for development. For production, `allow_origins` would be restricted to the Vercel deployment URL.

**Defensive Schema Validation & Unit Testing:**
In addition to range checking (`min <= default <= max`), we added strict integer-type validation. If `type == "integer"`, all numerical bounds (`default`, `min`, `max`, `step`) must be whole numbers. This prevents invalid float parameter bounds for discrete quantities like bolt counts and rib numbers. A dedicated test suite (`test_schemas.py`) was created to verify both valid configurations and failure-path rejections (such as out-of-range defaults and fractional integers).

**BackgroundTasks integration:**
```python
@app.post("/api/generate", response_model=GenerateResponse)
async def generate_part(payload: GenerateRequest, background_tasks: BackgroundTasks):
    # ... generation logic ...
    background_tasks.add_task(
        ArtifactCleanupManager.cleanup_old_artifacts
    )
    return response
```
`BackgroundTasks` fires after the HTTP response is sent, so cleanup never adds latency to the client-facing request time. This is the correct FastAPI pattern — using a thread pool (`asyncio.to_thread`) would also work but adds unnecessary complexity here since file I/O is fast.

### 2.4 Structured Logging

```python
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cad_workbench.main")
```

Each service module gets its own named logger:
- `cad_workbench.main` — HTTP routes
- `cad_workbench.cad_runner` — subprocess execution
- `cad_workbench.rag_service` — RAG retrieval
- `cad_workbench.llm_service` — LLM calls and fallbacks

**Why named loggers matter:** When debugging a failed generation at 2am, you want log lines like `[CAD] Script failed | error_type=runtime | stderr_head=...` not a wall of `print()` statements with no context. Named hierarchical loggers also allow per-module log-level filtering in production.

### 2.5 What Is NOT in Week 2 (Corrected Claims)

**Semaphore:** `asyncio.Semaphore` was discussed but not implemented. The actual concurrency strategy is:
- FastAPI's async event loop handles many concurrent connections natively
- `asyncio.to_thread` in `cad_runner.py` offloads blocking `subprocess.run` calls to the thread pool
- The thread pool size (default: `min(32, os.cpu_count() + 4)`) is the effective concurrency limit
- This is simpler and correct for this project's scale. A Semaphore would be appropriate if we needed to hard-cap at, say, 2 concurrent CAD subprocesses, but that was never a measured requirement.

**`/api/download` endpoint:** Files are served via `StaticFiles` at `/static/models/`. The frontend constructs the download URL from the `mesh_url` and `step_url` fields in the response. A dedicated download endpoint would add no value here — the static file server is sufficient and more efficient.

---

## 3. Technology Used

| Technology | Purpose |
|---|---|
| Pydantic v2 (`@model_validator`) | Schema validation with cross-field assertions |
| FastAPI `BackgroundTasks` | Post-response artifact cleanup without latency impact |
| FastAPI `CORSMiddleware` | Cross-origin headers for React dev server on :5173 |
| FastAPI `StaticFiles` | Efficient static file serving for STL/STEP downloads |
| `pathlib.Path.glob()` | Cross-platform file scanning for cleanup |
| `logging` (stdlib) | Structured, named, level-filtered application logging |

---

## 4. Key Design Decisions

### `DualOutputPayload` — The Core API Contract
The decision to require the LLM to produce both `python_code` and `parameters` in one JSON response (rather than separate calls) is the central design decision of the whole project. It means:
- One LLM call per generation (faster, cheaper, fewer failure modes)
- The parameter schema is always in sync with the code (no drift)
- The UI can render sliders without a second request
- Chat-to-Modify can pass the existing parameters back to the LLM for continuity

### Schema-Level Validation (`@model_validator`)
Catching `min > max` or `default out of range` at the Pydantic layer means:
- LLM output is rejected with a clear 422 error immediately
- The self-correction loop receives the specific validation failure as context
- The frontend never receives inconsistent slider bounds

---

## 5. What Is Missing / Could Be Improved

### ❌ Semaphore Not Implemented
The original plan mentioned concurrency limiting. The current implementation has no hard cap on concurrent CAD subprocesses. If 20 users hit `/api/generate` simultaneously, 20 `build123d` subprocesses would spawn. On a 4-core machine, this would degrade performance. A proper fix:

```python
# In main.py — add this at module level:
_CAD_SEMAPHORE = asyncio.Semaphore(max(1, (os.cpu_count() or 2) - 1))

# In execute_script_async:
async with _CAD_SEMAPHORE:
    returncode, stdout, stderr = await asyncio.wait_for(
        asyncio.to_thread(_run_script), timeout=timeout_seconds + 5
    )
```

This is a **carry-over item** that should be added before load testing in Week 11.

### ❌ No Test for Failure Path
`test_api.py` tests happy paths only. There is no test that sends a script with a `SyntaxError` and verifies `error_type == "syntax"` in the response. With the `ErrorType` classification added in Week 8, this is now testable.

### ❌ Cleanup Not Verified in Tests
The exit criteria claims "files purged after 2 hours" was verified. There is no test artefact for this. A simple test would be: write a file, backdate its `mtime` by 25 hours, call `cleanup_old_artifacts()`, assert the file is gone.

---

## 6. Files Created / Modified

| File | Location | Action |
|---|---|---|
| `schemas.py` | `backend/schemas.py` | Created — all Pydantic models |
| `cleanup.py` | `backend/services/cleanup.py` | Created — two-tier cleanup manager |
| `main.py` | `backend/main.py` | Expanded — CORS, BackgroundTasks, startup event |
| `requirements.txt` | `backend/requirements.txt` | Created — pinned dependencies |

---

## 7. Exit Criteria vs. Actual Result

| Criterion | Target | Actual |
|---|---|---|
| Pydantic schema validates LLM response | ✅ | ✅ Enforced via `DualOutputPayload` + `@model_validator` |
| Old artifacts cleaned automatically | ✅ | ✅ `cleanup_old_artifacts(86400s)` called via `BackgroundTasks` |
| CORS allows React dev server | ✅ | ✅ `allow_origins=["*"]`, `allow_credentials=False` |
| Structured logging throughout | ✅ | ✅ Named loggers per module |
| Semaphore concurrency limiting | ✅ (planned) | ❌ Not implemented — carry-over to Week 11 |
| Concurrent stress test verified | ✅ (claimed) | ❌ Not formally tested — no artefact |
| `/api/download` endpoint | ✅ (claimed) | ❌ Not needed — `StaticFiles` is equivalent |
