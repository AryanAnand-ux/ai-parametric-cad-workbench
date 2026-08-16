# Week 6 — Full End-to-End Pipeline, Sub-Second Recompute & Windows Stability Architecture

> **One-line goal:** Connect the full loop — user types a natural language prompt, a 3D model appears in the browser, parameter sliders are dynamically rendered, and dragging a slider recomputes the OpenCASCADE solid in sub-second time without LLM overhead, running stably across Windows, macOS, and Linux.

---

## 1. Framing & Architecture Overview

By Week 5, the project had all core modular subsystems:
- Backend: `build123d` solid kernel, AST security sandbox (with dangerous builtin blocking), ChromaDB RAG vector store (50 examples), and 4-tier LLM fallback.
- Frontend: React 18, React Three Fiber WebGL canvas with FOV auto-framing, and parametric slider controls.

Week 6 was the integration milestone where all isolated parts merged into a cohesive, interactive desktop application. This revealed three critical platform and lifecycle challenges:
1. **The Windows `NotImplementedError` Crash:** `asyncio.create_subprocess_exec` crashes on Windows under uvicorn's event loop.
2. **Uvicorn Auto-Reload Storms:** Writing temporary scripts inside the repository triggered immediate server reboots.
3. **Low-Latency Parametric Tuning:** Users modifying dimensions cannot wait 10–15 seconds for an LLM round-trip; parametric recomputation must bypass the LLM entirely and execute in hundreds of milliseconds.

```
                                 END-TO-END WORKBENCH PIPELINE
                                 
  [ USER TEXT PROMPT ]  ──►  POST /api/generate
                                   │
                                   ▼
                      ┌───────────────────────────┐
                      │ 1. ChromaDB RAG Search    │ ──► Top-3 few-shot examples
                      │ 2. 4-Tier LLM Fallback    │ ──► DualOutputPayload JSON
                      │ 3. AST Security Sandbox   │ ──► Verify imports & builtins
                      │ 4. Subprocess Execution   │ ──► asyncio.to_thread (Win-safe)
                      │ 5. trimesh Mesh Check     │ ──► Watertight & volume check
                      └─────────────┬─────────────┘
                                    │
                                    ▼ Return {mesh_url, parameters, python_code}
                      ┌───────────────────────────┐
                      │    React 18 Frontend      │
                      │ • Render WebGL 3D Mesh    │
                      │ • Auto-frame FOV camera   │
                      │ • Render ParameterSliders │
                      └─────────────┬─────────────┘
                                    │
                                    │ User drags slider (e.g. length = 80mm)
                                    ▼
                      ┌───────────────────────────┐
                      │ Frontend 100ms Debounce   │
                      └─────────────┬─────────────┘
                                    │
                                    ▼ POST /api/recompute (NO LLM INVOLVED)
                      ┌───────────────────────────┐
                      │ Fast Parameter Injector   │
                      │ • Brace-counting parser   │
                      │ • Swap PARAMS dict values │
                      │ • Re-run build123d script │
                      │ • Return updated .stl     │
                      └─────────────┬─────────────┘
                                    │ (Total time: ~300ms)
                                    ▼
                      [ WebGL Canvas Updates Live ]
```

---

## 2. What Was Built

### 2.1 Cross-Platform Async Subprocess Runner (`cad_runner.py`)

**The Windows Event Loop Gotcha:**
On Windows with Python 3.12, uvicorn runs `SelectorEventLoop` by default. Invoking `asyncio.create_subprocess_exec` raises `NotImplementedError: create_subprocess_exec`. Changing the global loop policy is fragile across operating systems.

**The Universal Thread-Pool Solution:**
We refactored `CADRunner.execute_script_async` to use `asyncio.to_thread` wrapping standard synchronous `subprocess.run`:

```python
def _run_script() -> tuple[int, str, str]:
    """Blocking subprocess call — runs safely inside a worker thread pool."""
    result = subprocess.run(
        [PYTHON_EXEC, str(temp_script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,  # 30s process-level timeout
    )
    return result.returncode, result.stdout, result.stderr

# Outer asyncio timeout guard (35s) ensures the thread pool never deadlocks
returncode, stdout, stderr = await asyncio.wait_for(
    asyncio.to_thread(_run_script),
    timeout=timeout_seconds + 5,
)
```

This pattern is non-blocking to the FastAPI event loop, enforces strict timeouts, and functions identically on Windows, Linux, and macOS.

### 2.2 Sub-Second Parameter Recompute Endpoint (`/api/recompute`)

To deliver an interactive CAD workbench experience, we implemented `/api/recompute` in `main.py`:

- **Zero LLM Overhead:** The endpoint accepts `script_id`, `python_code`, and `updated_parameters`.
- **Stateful Parameter Injection:** `CADRunner.inject_parameters()` updates the `PARAMS = {...}` dictionary in-memory using the brace-counting parser.
- **Direct Kernel Execution:** The updated script executes directly via `CADRunner.execute_script_async()`.
- **Execution Time:** Drops end-to-end latency from ~10,000ms (LLM generation) to **150–400ms** (pure OpenCASCADE CSG evaluation and STL export).

### 2.3 Frontend Debounce & Slider Coordination (`App.jsx`)

To prevent flooding the server during continuous slider dragging:

- Implemented a 100ms debounce buffer in `App.jsx`.
- When the user drags a slider, local UI state updates immediately (60fps track fill and numerical readout).
- The network request to `/api/recompute` is dispatched only when slider movement settles for 100ms.
- Replaced STL geometry is loaded seamlessly into the active Three.js canvas with zero full-page reload.

### 2.4 Uvicorn Reload Loop Resolution & Config Isolation (`config.py`)

When running with `uvicorn --reload`, file changes trigger server restarts. Because earlier implementations generated temp `.py` scripts inside `backend/`, every generation request caused an infinite server restart loop.

**Fix in `config.py`:**
```python
BASE_DIR   = Path(__file__).resolve().parent
TEMP_DIR   = BASE_DIR.parent / "scratch" / "temp"   # Located OUTSIDE backend source tree
MODELS_DIR = BASE_DIR.parent / "scratch" / "models"

TEMP_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
```
In addition, uvicorn startup commands were configured with `--reload-exclude "*.stl" --reload-exclude "*.step"`.

### 2.5 Pre-Flight Boot Validation (`startup_check.py`)

Created a startup sanity checker that executes before the API accepts incoming connections:
1. Verifies `GEMINI_API_KEY` and `GROQ_API_KEY` presence in `.env`.
2. Tests `build123d` and OpenCASCADE imports.
3. Automatically triggers `RAGService.build_index()` to ensure the 50-example ChromaDB index is warmed up in local storage.

---

## 3. Technology Used

| Component | Technology | Purpose |
|---|---|---|
| Async Concurrency | `asyncio.to_thread` | Offloading synchronous process execution without event loop crashes |
| Process Execution | `subprocess.run` | Isolated child process execution with stdout/stderr capture |
| Web API Framework | `FastAPI` (v0.115+) | High-speed async routes (`/api/generate`, `/api/recompute`) |
| Debounce Logic | Custom `useCallback` / Timer | 100ms frontend request batching |
| 3D Graphics | `Three.js` + `STLLoader` | Dynamic in-canvas mesh replacement |

---

## 4. Key Problems Solved (with Technical Details)

### Problem 1: Windows Subprocess Event Loop `NotImplementedError`

**Root Cause:** The default Windows asyncio `SelectorEventLoop` does not implement asynchronous subprocess pipes.

**Solution:** Moving to `asyncio.to_thread(subprocess.run, ...)` completely bypasses asyncio subprocess internals by running synchronous `subprocess.run` on a separate OS thread, while remaining 100% async-compatible with FastAPI.

### Problem 2: Parameter Slider Latency Bottleneck

**Root Cause:** Re-prompting the LLM for simple dimensional changes (e.g. changing plate length from 40mm to 60mm) takes 8–15 seconds and frequently mutates unrelated geometry.

**Solution:** Direct string-level parameter injection via `/api/recompute` eliminates the LLM from the loop, preserving 100% geometric topology and delivering sub-second response times.

---

## 5. Files Created / Modified

| File | Location | Description |
|---|---|---|
| `main.py` | `backend/main.py` | Implemented `/api/recompute`, startup events, static mounts |
| `cad_runner.py` | `backend/services/cad_runner.py` | Cross-platform `asyncio.to_thread` executor, 30s timeout guards |
| `config.py` | `backend/config.py` | Isolated `TEMP_DIR` and `MODELS_DIR` outside backend source tree |
| `startup_check.py` | `backend/startup_check.py` | Boot pre-flight validation and ChromaDB index warm-up |
| `App.jsx` | `frontend/src/App.jsx` | Connected generation form, slider debounce, recompute handler |

---

## 6. What Was Missing / Improved in Subsequent Weeks

1. **Neobrutalism UI & Code Inspector (Addressed in Week 7):**
   - Week 6 had functional UI elements but lacked design polish, preset chips, and a Python code inspection drawer.
   - *Fix:* Implemented in Week 7.

2. **Chat-to-Modify (Addressed in Week 7):**
   - Changing topological features (e.g. "add 4 mounting holes to the corners") still required a fresh `/api/generate` call.
   - *Fix:* Added `/api/modify` endpoint in Week 7.

3. **Solid-First CSG Rules (Addressed in Week 8):**
   - Parameter recomputation revealed edge cases where certain LLM scripts generated disconnected bodies when dimensions expanded.
   - *Fix:* Implemented the 15-Rule Solid-First CSG spec and multi-body graph validation in Week 8.

---

## 7. Exit Criteria vs. Actual Result

| Criterion | Target | Actual |
|---|---|---|
| End-to-end generation from prompt to 3D | ✅ | ✅ Verified on manual test prompts |
| Dynamic slider generation from JSON schema | ✅ | ✅ UI sliders auto-populate with units and ranges |
| Sub-second slider recomputation | ✅ | ✅ `/api/recompute` executes in 150–400ms |
| 100ms slider debouncing | ✅ | ✅ Prevents backend overload during drag events |
| Windows stability (no `NotImplementedError`) | ✅ | ✅ Verified on Windows 11 with Python 3.12 |
| Uvicorn reload loops prevented | ✅ | ✅ Temp files isolated outside backend directory |
