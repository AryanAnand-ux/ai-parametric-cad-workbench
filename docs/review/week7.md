# Week 7 — Chat-to-Modify Architecture, Endpoint Invariants & Soft Neobrutalism UI

> **One-line goal:** Implement conversational CAD script refinement (`/api/modify`), establish strict endpoint architectural invariants across generation, modification, and recomputation, and overhaul the user interface into a high-contrast "Soft Neobrutalism" design system with a Python code inspector drawer and preset chips.

---

## 1. Framing & Architecture Overview

By Week 6, the system could generate 3D models from scratch and tune numerical dimensions in real-time via `/api/recompute`. However, if a user wanted a topological or structural modification (e.g. *"add 4 corner mounting holes"* or *"make the center hollow with a 3mm lip"*), sliders could not help.

Week 7 delivered two major milestones:
1. **Chat-to-Modify Pipeline (`/api/modify`):** Conversational AI refinement that accepts the current Python code, part metadata, existing parameters, and a natural language delta prompt to modify the CAD model while preserving existing design variables.
2. **Endpoint Invariant Architecture:** Defined explicit contracts for the three execution paths (`/generate`, `/modify`, `/recompute`) to ensure security, schema compliance, and timeout safety across all operations.
3. **Soft Neobrutalism UI System:** Upgraded the visual interface with 2.5px solid borders, tactical 4px offset shadows, `Space Grotesk` typography, preset chips, and a slide-out Python Code Inspector drawer.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   THREE MUTATION PATHS & THEIR INVARIANTS             │
├───────────────────┬────────────────────────────────────────────────────┤
│ 1. /api/generate  │ • Starts fresh from a text prompt                  │
│                   │ • RAG vector retrieval (top-3 from 50 examples)    │
│                   │ • 4-tier LLM fallback → DualOutputPayload          │
│                   │ • AST Security Sandbox (imports + builtins)        │
│                   │ • Subprocess (30s timeout) + 3 self-corrections    │
├───────────────────┼────────────────────────────────────────────────────┤
│ 2. /api/modify    │ • Preserves existing script structure & PARAMS     │
│    (Chat-to-Modify│ • LLM receives current code + delta prompt         │
│                   │ • Enforces SAME DualOutputPayload Pydantic schema  │
│                   │ • Enforces SAME AST Security Sandbox               │
│                   │ • Enforces SAME 3-retry self-correction loop       │
├───────────────────┼────────────────────────────────────────────────────┤
│ 3. /api/recompute │ • Bypasses LLM entirely (zero token / API cost)    │
│    (Live Sliders) │ • In-memory PARAMS swap via brace-counting parser  │
│                   │ • Direct OpenCASCADE kernel execution (150–400ms)  │
│                   │ • Enforces 30s subprocess timeout                  │
└───────────────────┴────────────────────────────────────────────────────┘
```

---

## 2. What Was Built

### 2.1 Chat-to-Modify Pipeline (`/api/modify` in `main.py` & `llm_service.py`)

Added conversational script editing:

- **Context-Preserving Prompting:** `MODIFY_PROMPT_TEMPLATE` formats the current `python_code`, `part_name`, and serialized `existing_parameters` JSON alongside the user's `modification_prompt`.
- **Versioned Script IDs:** Generates tracked revision IDs (e.g. `bracket_123_v1`, `bracket_123_v2`) to preserve history and prevent cache collisions.
- **Strict Validation Parity:** The modified output is parsed through `_parse_response`, validating `DualOutputPayload` Pydantic constraints and running `validate_script_safety` prior to execution.
- **Self-Correction on Modifications:** If the LLM's modification introduces a syntax or OpenCASCADE boolean error, the self-correction loop automatically triggers up to 3 retries with the traceback.

```python
# System prompt formatting in services/prompts.py
MODIFY_PROMPT_TEMPLATE = """You are modifying an existing build123d Python script.
Current Part: {part_name}
User Modification Request: {modification_prompt}

Current Python Code:
```python
{python_code}
```

Existing Parameters:
{existing_parameters_json}

INSTRUCTIONS:
1. Apply the user's requested changes while preserving existing design variables where possible.
2. Ensure the script begins with a valid PARAMS = {{...}} block.
3. Return a valid JSON object matching the DualOutputPayload schema.
"""
```

### 2.2 Security Status & Builtin Blocking (`services/cad_runner.py`)

The AST security sandbox (`validate_script_safety`) actively protects all execution paths against both disallowed imports and unimported dangerous built-ins:

```python
ALLOWED_IMPORTS = {
    "build123d", "math", "typing", "types",
    "collections", "itertools", "functools",
    "enum", "dataclasses", "abc", "operator"
}

BLOCKED_BUILTINS = {
    "open", "eval", "exec", "compile", "__import__", "input",
    "globals", "locals", "getattr", "setattr", "delattr", "system",
    "breakpoint", "memoryview"
}

BLOCKED_ATTRIBUTES = {
    "__subclasses__", "__bases__", "__globals__",
    "__code__", "__reduce__", "__reduce_ex__", "__mro__"
}
```
*Verification:* 7 dedicated unit tests in `test_ast_security.py` confirm that unauthorized imports (`os`, `sys`, `subprocess`), dangerous builtins (`open()`, `eval()`, `exec()`, `input()`), and reflection exploits (`__subclasses__`, `__globals__`) are intercepted before process spawning.

### 2.3 High-Precision Timing Telemetry

Added `time.perf_counter()` logging across all routes in `main.py`:
- `[GENERATE] Success | model=gemini-2.5-flash | time=8790ms | corrections=0`
- `[RECOMPUTE] Success | script_id=bracket_123 | time=245ms | dims={'x': 75.0, 'y': 25.0, 'z': 15.0}`
- `[MODIFY] Success | script_id=bracket_123_v1 | time=9120ms | model=gemini-2.5-flash`

### 2.4 Soft Neobrutalism UI Design System (`frontend/src/index.css`)

Redesigned the frontend into a technical, high-contrast engineering interface:

- **Neobrutalist CSS Tokens:**
  - `2.5px solid #18181B` borders on all cards, inputs, and buttons.
  - Hard offset drop shadows: `box-shadow: 4px 4px 0 #18181B`.
  - Active button tactile depression: `transform: translate(2px, 2px); box-shadow: 2px 2px 0 #18181B`.
- **Typography:** Integrated Google Fonts `Space Grotesk` (weights 400, 600, 700) for a modern CAD aesthetic.
- **Preset Quick-Launch Chips:** Added one-click component chips in `App.jsx`:
  - 🛸 *Drone Frame*
  - 📐 *Mounting Bracket*
  - ⚙️ *Gear Blank*
  - 📦 *Enclosure Box*
  - 🔘 *Shaft Collar*
- **Python Code Inspector Drawer:**
  - Added `GET /api/script/{id}` endpoint to retrieve raw script source.
  - Built a slide-out code drawer in the UI allowing engineers to inspect the exact `build123d` Python code generating the 3D model.

---

## 3. Technology Used

| Layer | Technology | Role |
|---|---|---|
| API Framework | **FastAPI** | `/api/modify`, `/api/script/{id}`, `/api/recompute` |
| Security Layer | **Python `ast` Module** | Static analysis checking imports, builtins, and dunders |
| Design Tokens | **CSS3 Variables & Flexbox** | Soft Neobrutalism design system (`index.css`) |
| Typography | **Google Fonts (Space Grotesk)** | Engineering-grade monospace/sans typography |
| 3D Lighting | **Three.js PCFSoftShadowMap** | Soft contact shadows and directional blueprint lighting |
| Client HTTP | **Axios (with Vite Proxy)** | Async API requests with error handling |

---

## 4. Key Problems Solved (with Technical Details)

### Problem 1: Structural Modification Without Losing Design Parameters

**Root Cause:** Prompting an LLM from scratch to "add holes to the bracket" often completely redrew the part with different overall dimensions, discarding existing slider variables.

**Solution:** In `LLMService.modify_script`, the existing `python_code` and serialized `parameters` array are injected into `MODIFY_PROMPT_TEMPLATE`. The LLM is explicitly instructed to mutate the geometry while preserving the top `PARAMS` dictionary keys, enabling continuous multi-turn CAD design refinement.

### Problem 2: Preserving Security Parity on Modification Calls

**Root Cause:** New endpoints can inadvertently bypass security checks if developers execute code directly without routing through the sandbox.

**Solution:** `/api/modify` strictly invokes `CADRunner.execute_script_async()`, ensuring that modified scripts are subjected to the exact same AST whitelist, builtin blocking, 30s timeout guards, and self-correction loop as newly generated scripts.

---

## 5. Files Created / Modified

| File | Location | Description |
|---|---|---|
| `main.py` | `backend/main.py` | Added `/api/modify`, `/api/script/{id}`, timing logging |
| `llm_service.py` | `backend/services/llm_service.py` | Added `modify_script` / `modify_code` workflow |
| `prompts.py` | `backend/services/prompts.py` | Added `MODIFY_PROMPT_TEMPLATE` with context preservation |
| `index.css` | `frontend/src/index.css` | Implemented Soft Neobrutalism design system & tokens |
| `App.jsx` | `frontend/src/App.jsx` | Added Chat-to-Modify panel, Code Inspector drawer, preset chips |
| `test_api.py` | `backend/test_api.py` | Full integration test for `/api/generate`, `/api/recompute`, `/api/modify` |

---

## 6. What Was Missing / Improved in Subsequent Weeks

1. **Solid-First CSG Rules (Addressed in Week 8):**
   - In Week 7, complex multi-arm models (like quadcopters) sometimes used 2D sketch `Line()` elements, causing OpenCASCADE to produce zero-area faces or disconnected geometry islands.
   - *Fix:* In Week 8, the prompt and validation layer were upgraded to the 15-Rule Solid-First CSG specification.

2. **Automated Multi-Body Graph Validation (Addressed in Week 8):**
   - The runner accepted any valid STL, even if boolean union failures created 4 floating disconnected bodies.
   - *Fix:* Added `trimesh.graph.connected_components` in Week 8 to guarantee exactly 1 solid body.

---

## 7. Exit Criteria vs. Actual Result

| Criterion | Target | Actual |
|---|---|---|
| Conversational CAD modification (`/api/modify`) | ✅ | ✅ Verified in `test_api.py` (modifies height, returns versioned ID) |
| Security parity across all execution routes | ✅ | ✅ `validate_script_safety` enforced on `/generate`, `/modify`, `/recompute` |
| High-precision timing telemetry logged | ✅ | ✅ `time.perf_counter()` logs execution duration on all routes |
| Soft Neobrutalism UI overhaul | ✅ | ✅ 2.5px borders, 4px shadows, Space Grotesk, preset chips |
| Python Code Inspector drawer | ✅ | ✅ Fetches and renders raw `.py` source via `/api/script/{id}` |
| Qualitative prompt self-correction rate | ✅ (~80–90% informal) | ✅ Tested across ~20 manual prompts; formal benchmark set for Week 11 |
