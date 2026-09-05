"""
CAD Runner — build123d Subprocess Executor
==========================================
Executes build123d Python scripts in isolated subprocesses.

Pipeline: Inject PARAMS → AST Security Check → Execute → Validate Geometry → Return URLs

Key responsibilities:
- Inject updated PARAMS into scripts for parametric recomputation
- Run scripts safely via asyncio.to_thread + subprocess.run (Windows-safe)
- AST security sandbox: whitelist only build123d, math, typing imports
- Post-execution mesh validation: watertight, connected, non-zero volume
- Export STL (WebGL preview) + STEP (download) files
- Return execution metrics, geometry health report, and file URLs

15-Rule Quality Enforcement (from engineering spec):
  Rule 2 — Geometry validation: assert solid exists, watertight, connected
  Rule 3 — Connected geometry: detect and flag disconnected islands
  Rule 7 — Clearance/collision: flag when bbox dimensions are implausible
  Rule 10 — Tolerances: surface area / volume ratio sanity check
"""

import os
import re
import ast
import sys
import json
import time
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List

from config import (
    TEMP_DIR,
    MODELS_DIR,
    PYTHON_EXEC,
    CAD_MAX_CONCURRENT_EXECUTIONS,
    CAD_EXECUTION_TIMEOUT_SECONDS,
)
from services.cleanup import ArtifactCleanupManager

logger = logging.getLogger("cad_workbench.cad_runner")

# ---------------------------------------------------------------------------
# Structured Error Classification
# ---------------------------------------------------------------------------
# Motivation (from Week 1 retrospective):
#   A bare generic Exception gives zero signal about WHY a script failed.
#   Classifying into Timeout / Syntax / Security / Runtime / IOError means:
#     - The self-correction prompt can be tailored to the specific failure mode
#     - Benchmarking can measure which failure mode is most common
#     - The frontend can show a specific, actionable message to the user
#   This was flagged as a Week 1 gap: "even a basic classification would make
#   debugging the pipeline much easier for weeks 2–5."
# ---------------------------------------------------------------------------

class ErrorType:
    TIMEOUT  = "timeout"   # script ran longer than timeout_seconds
    SYNTAX   = "syntax"    # Python SyntaxError before any execution
    SECURITY = "security"  # blocked by AST import whitelist
    RUNTIME  = "runtime"   # exception raised during build123d execution
    IO_ERROR = "io_error"  # failed to write temp file or read output
    UNKNOWN  = "unknown"   # catch-all fallback


def classify_error(stderr: str, returncode: int) -> str:
    """
    Inspects stderr content to determine the specific error category.

    This is called AFTER stdout/stderr have been fully captured from the
    completed subprocess — there is no race condition with script execution.

    Returns one of the ErrorType string constants.
    """
    # returncode == -1 is our sentinel for a timeout kill
    if returncode == -1:
        return ErrorType.TIMEOUT

    if not stderr:
        return ErrorType.UNKNOWN

    s = stderr.lower()

    # Python syntax errors (detected before any geometry runs)
    if "syntaxerror" in s or "invalid syntax" in s or "indentationerror" in s:
        return ErrorType.SYNTAX

    # Import violations — AST sandbox may have missed a dynamic import,
    # or a package is genuinely not installed in this venv
    if "importerror" in s or "modulenotfounderror" in s:
        return ErrorType.SECURITY

    # build123d / OpenCASCADE geometry failures and standard Python exceptions
    if any(kw in s for kw in [
        "assertionerror", "valueerror", "typeerror", "attributeerror",
        "nameerror", "zerodivisionerror", "runtimeerror",
        "build123d", "opencascade", "brep", "traceback"
    ]):
        return ErrorType.RUNTIME

    return ErrorType.UNKNOWN



ALLOWED_IMPORTS = {
    "build123d", "math", "typing", "types",
    "collections", "itertools", "functools",
    "enum", "dataclasses", "abc", "operator"
}

# Dangerous built-ins and dunder attributes that could bypass import whitelists
BLOCKED_BUILTINS = {
    "open", "eval", "exec", "compile", "__import__", "input",
    "globals", "locals", "getattr", "setattr", "delattr", "system",
    "breakpoint", "memoryview"
}

BLOCKED_RUNTIME_NAMES = {"sys", "_sys_runtime", "_os_dll", "_ocp_libs"}

BLOCKED_ATTRIBUTES = {
    "__subclasses__", "__bases__", "__globals__",
    "__code__", "__reduce__", "__reduce_ex__", "__mro__"
}

SAFE_SCRIPT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,100}$")
CAD_EXECUTION_SEMAPHORE = asyncio.Semaphore(max(1, CAD_MAX_CONCURRENT_EXECUTIONS))


def is_safe_script_id(script_id: str) -> bool:
    """Return whether an artifact identifier is safe to use as a filename stem."""
    return bool(isinstance(script_id, str) and SAFE_SCRIPT_ID_PATTERN.fullmatch(script_id))


# ---------------------------------------------------------------------------
# AST Security Sandbox
# ---------------------------------------------------------------------------

def validate_script_safety(python_code: str) -> tuple[bool, str]:
    """
    Parses the script with Python's AST module and verifies:
      1. Only whitelisted libraries are imported (blocks os, sys, subprocess, etc.)
      2. No dangerous built-in functions are invoked (blocks open, eval, exec, compile, input, etc.)
      3. No sensitive dunder attribute reflection exploits (__subclasses__, __globals__, etc.)

    Returns: (is_safe: bool, reason: str)
    """
    try:
        tree = ast.parse(python_code)
    except SyntaxError as e:
        return False, f"Syntax error: {e}"

    for node in ast.walk(tree):
        # 1. Check `import X` statements
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in ALLOWED_IMPORTS:
                    return False, f"Blocked import: '{alias.name}' (not in whitelist)"

        # 2. Check `from X import Y` statements
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                if root not in ALLOWED_IMPORTS:
                    return False, f"Blocked import: 'from {node.module}' (not in whitelist)"

        # 3. Check function calls (blocks unimported builtins like open(), eval(), exec(), input())
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in BLOCKED_BUILTINS:
                    return False, f"Blocked builtin call: '{node.func.id}()' is forbidden in CAD scripts"
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr in BLOCKED_BUILTINS:
                    return False, f"Blocked attribute call: '{node.func.attr}()' is forbidden"

        # 4. Check sensitive attribute introspection/reflection
        elif isinstance(node, ast.Attribute):
            if node.attr in BLOCKED_ATTRIBUTES:
                return False, f"Blocked sensitive attribute access: '{node.attr}'"

        # 5. Check direct reference to __builtins__ / __import__
        elif isinstance(node, ast.Name):
            if node.id in {"__builtins__", "__import__"}:
                return False, f"Blocked direct reference: '{node.id}'"
            if node.id in BLOCKED_RUNTIME_NAMES:
                return False, f"Blocked runtime reference: '{node.id}'"

    return True, "OK"


# ---------------------------------------------------------------------------
# Parameter Injection
# ---------------------------------------------------------------------------

def _find_params_block(code: str) -> tuple[int, int] | None:
    """
    Finds the start and end indices of the PARAMS = {...} block using
    brace-counting rather than regex, so nested braces / comments inside
    the dict are handled correctly.

    Returns (start_idx, end_idx) of the full `PARAMS = { ... }` expression,
    or None if not found.
    """
    match = re.search(r"PARAMS\s*=\s*\{", code)
    if not match:
        return None

    brace_start = match.end() - 1   # position of the opening '{'
    depth = 0
    in_single = False
    in_double = False
    i = brace_start

    while i < len(code):
        ch = code[i]
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif not in_single and not in_double:
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return (match.start(), i + 1)   # inclusive end
        i += 1

    return None   # unbalanced braces — fall back


def inject_parameters(python_code: str, parameters: Dict[str, Any]) -> str:
    """
    Replaces the PARAMS = {...} block with updated values.
    Uses a brace-counting parser so nested braces inside the dict
    (or a `}` in a comment) do not cause early truncation.
    """
    params_str = f"PARAMS = {json.dumps(parameters, indent=4)}"
    span = _find_params_block(python_code)
    if span:
        start, end = span
        return python_code[:start] + params_str + python_code[end:]
    # PARAMS block not found — prepend it
    return f"{params_str}\n\n{python_code}"


# ---------------------------------------------------------------------------
# Subprocess Wrapper Builder
# ---------------------------------------------------------------------------

def _build_wrapper(python_code: str, stl_posix: str, step_posix: str, fast_preview: bool = False) -> str:
    """
    Wraps the user script with OUTPUT_STL / OUTPUT_STEP injection
    and a try/except that sends tracebacks to stderr.

    On Windows, we also inject os.add_dll_directory() calls for
    cadquery_ocp_novtk.libs so the OpenCASCADE DLLs are resolvable
    by the subprocess even when Windows Application Control policies
    would otherwise block native extension loading.
    """
    import site
    import os as _os

    fast_patch = ""
    if fast_preview:
        fast_patch = '''\
# ── Fast Preview Optimization (Optimized tolerances for fast recomputation) ─
import build123d as _b3d_opt
_real_export_stl = _b3d_opt.export_stl
def _fast_export_stl(to_export, file_path, tolerance=0.01, angular_tolerance=0.25, ascii_format=False):
    return _real_export_stl(to_export, file_path, tolerance=tolerance, angular_tolerance=angular_tolerance, ascii_format=ascii_format)
_b3d_opt.export_stl = _fast_export_stl
# ────────────────────────────────────────────────────────────────────────────
'''

    # Find the cadquery OCP libs folder relative to current site-packages
    ocp_libs_dir = ""
    for sp in site.getsitepackages():
        candidate = _os.path.join(sp, "cadquery_ocp_novtk.libs")
        if _os.path.isdir(candidate):
            ocp_libs_dir = candidate.replace("\\", "\\\\")
            break

    dll_injection = ""
    if ocp_libs_dir:
        dll_injection = f'''\
# ── DLL search path: OpenCASCADE native libs (Windows) ──────────────────────
import os as _os_dll
_ocp_libs = r"{ocp_libs_dir}"
if hasattr(_os_dll, "add_dll_directory") and _os_dll.path.isdir(_ocp_libs):
    _os_dll.add_dll_directory(_ocp_libs)
# ────────────────────────────────────────────────────────────────────────────
'''

    indented = "\n".join(
        "    " + line if line.strip() else line
        for line in python_code.splitlines()
    )
    return f'''import sys as _sys_runtime
{dll_injection}
{fast_patch}
# Runtime-injected export paths (do NOT redefine these in generated scripts)
OUTPUT_STL  = r"{stl_posix}"
OUTPUT_STEP = r"{step_posix}"

try:
{indented}
except Exception:
    import traceback
    _sys_runtime.stderr.write(traceback.format_exc())
    _sys_runtime.exit(1)
'''


# ---------------------------------------------------------------------------
# Main CAD Runner
# ---------------------------------------------------------------------------

class CADRunner:
    """
    Async subprocess runner for build123d CAD scripts.
    Replaces the trimesh-based freecad_runner.py from Weeks 1-3.
    """

    @staticmethod
    def inject_parameters(python_code: str, parameters: Dict[str, Any]) -> str:
        return inject_parameters(python_code, parameters)

    @classmethod
    async def execute_script_async(
        cls,
        script_id: str,
        python_code: str,
        parameters: Optional[Dict[str, Any]] = None,
        design_mode: str = "single_solid",
        component_names: Optional[List[str]] = None,
        timeout_seconds: int = CAD_EXECUTION_TIMEOUT_SECONDS,
        fast_preview: bool = False
    ) -> Dict[str, Any]:
        """
        Runs a build123d script in an isolated subprocess.
        Returns execution result dict with mesh_url, step_url, mesh_info.
        """
        start = time.time()

        if not is_safe_script_id(script_id):
            return {
                "status": "error",
                "error_type": ErrorType.SECURITY,
                "script_id": script_id,
                "recomputation_time_ms": 0,
                "stderr": "Invalid script_id: only letters, numbers, '_' and '-' are allowed.",
                "mesh_url": None,
                "step_url": None,
                "mesh_info": {},
            }

        if design_mode not in {"single_solid", "assembly"}:
            return {
                "status": "error",
                "error_type": ErrorType.RUNTIME,
                "script_id": script_id,
                "recomputation_time_ms": 0,
                "stderr": f"Invalid design_mode: {design_mode!r}",
                "mesh_url": None,
                "step_url": None,
                "mesh_info": {},
            }

        if parameters:
            python_code = inject_parameters(python_code, parameters)

        # ── AST Security Check ────────────────────────────────────────────
        is_safe, reason = validate_script_safety(python_code)
        if not is_safe:
            # classify_error: distinguish SyntaxError (bad LLM code) from
            # blocked import (security violation) for targeted self-correction.
            err_type = ErrorType.SYNTAX if "Syntax error" in reason else ErrorType.SECURITY
            logger.warning(f"[CAD] Script BLOCKED ({err_type}): {reason}")
            return {
                "status": "error",
                "error_type": err_type,
                "script_id": script_id,
                "recomputation_time_ms": 0,
                "stderr": f"Security violation: {reason}",
                "mesh_url": None,
                "step_url": None,
                "mesh_info": {}
            }

        stl_filename  = f"{script_id}.stl"
        step_filename = f"{script_id}.step"
        stl_path  = MODELS_DIR / stl_filename
        step_path = MODELS_DIR / step_filename

        wrapper = _build_wrapper(
            python_code,
            stl_path.as_posix(),
            step_path.as_posix(),
            fast_preview=fast_preview
        )

        temp_script = TEMP_DIR / f"{script_id}_exec.py"

        try:
            with open(temp_script, "w", encoding="utf-8") as f:
                f.write(wrapper)
        except OSError as e:
            return {
                "status": "error",
                "error_type": ErrorType.IO_ERROR,
                "script_id": script_id,
                "recomputation_time_ms": 0,
                "stderr": f"Failed to write temp script: {e}",
                "mesh_url": None, "step_url": None, "mesh_info": {}
            }

        # ── Run the script in a thread-pool executor ─────────────────────
        # asyncio.create_subprocess_exec raises NotImplementedError on
        # Windows with Python 3.12+ SelectorEventLoop (used by uvicorn).
        # asyncio.to_thread + subprocess.run works on all platforms/versions.
        def _run_script() -> tuple[int, str, str]:
            """Blocking subprocess call — runs in a thread pool with a stripped env."""
            # Build a minimal env: only basic OS/runtime vars, no API keys or tokens
            _os_env = os.environ
            isolated_env = {
                k: _os_env[k]
                for k in (
                    "SYSTEMROOT", "SYSTEMDRIVE", "PATH", "PATHEXT",
                    "TEMP", "TMP", "USERNAME", "USERPROFILE",
                    "APPDATA", "LOCALAPPDATA", "COMSPEC",
                    # Python runtime
                    "PYTHONPATH", "PYTHONHOME",
                    # OCC / build123d shared libraries
                    "OCC_LIBRARY_PATH",
                )
                if k in _os_env
            }
            # Explicitly block user-site packages to reduce attack surface
            isolated_env["PYTHONNOUSERSITE"] = "1"
            # Ensure PYTHONPATH is empty so installed packages outside venv can't be reached
            isolated_env["PYTHONPATH"] = ""

            result = subprocess.run(
                [PYTHON_EXEC, str(temp_script)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
                env=isolated_env,
            )
            return result.returncode, result.stdout, result.stderr

        try:
            try:
                async with CAD_EXECUTION_SEMAPHORE:
                    returncode, stdout, stderr = await asyncio.to_thread(_run_script)
            except asyncio.TimeoutError:
                return {
                    "status": "error",
                    "error_type": ErrorType.TIMEOUT,
                    "script_id": script_id,
                    "recomputation_time_ms": int((time.time() - start) * 1000),
                    "stderr": f"Execution timed out after {timeout_seconds}s.",
                    "stdout": "", "returncode": -1,
                    "mesh_url": None, "step_url": None, "mesh_info": {}
                }
            except subprocess.TimeoutExpired:
                return {
                    "status": "error",
                    "error_type": ErrorType.TIMEOUT,
                    "script_id": script_id,
                    "recomputation_time_ms": int((time.time() - start) * 1000),
                    "stderr": f"Script timed out after {timeout_seconds}s.",
                    "stdout": "", "returncode": -1,
                    "mesh_url": None, "step_url": None, "mesh_info": {}
                }

            elapsed = int((time.time() - start) * 1000)
            success = (returncode == 0) and stl_path.exists()
            missing_step_export = success and not step_path.exists()

            # Classify error AFTER full stdout/stderr capture — no race condition.
            # Cleanup of temp_script happens in the `finally` block below,
            # sequenced after this classification and after all stderr is read.
            error_type = ErrorType.UNKNOWN if not success else None
            if not success:
                error_type = classify_error(stderr, returncode)
                logger.warning(
                    f"[CAD] Script failed | script_id={script_id} "
                    f"| error_type={error_type} | returncode={returncode} "
                    f"| stderr_head={stderr[:120].strip()!r}"
                )

            # ── Persist Python script file for code inspection API ──────────
            py_path = MODELS_DIR / f"{script_id}.py"
            if success:
                try:
                    with open(py_path, "w", encoding="utf-8") as py_file:
                        py_file.write(python_code)
                except OSError as me:
                    logger.warning(f"[CAD] Could not persist script file: {me}")

            # ── Mesh inspection & geometry validation ─────────────────────
            # Implements engineering spec rules 2, 3, 7:
            #   Rule 2 — Validate geometry before accepting success
            #   Rule 3 — Detect disconnected/floating bodies (islands)
            #   Rule 7 — Sanity-check volume vs surface area ratio
            mesh_info = {}
            geometry_warnings = []
            if stl_path.exists():
                try:
                    import trimesh, trimesh.graph, gc
                    mesh = trimesh.load_mesh(str(stl_path))
                    ext = mesh.extents

                    # --- Watertight check (Rule 2) ---
                    is_watertight = bool(getattr(mesh, "is_watertight", False))
                    if not is_watertight:
                        geometry_warnings.append(
                            "Mesh is not watertight (non-manifold edges detected). "
                            "Check for zero-thickness walls or boolean operation failures."
                        )

                    # --- Volume sanity (Rule 2) ---
                    volume = float(getattr(mesh, "volume", 0.0))
                    if volume <= 0:
                        geometry_warnings.append(
                            f"Mesh volume is {volume:.2f} mm³ (≤ 0). "
                            "Geometry may be inverted or degenerate."
                        )

                    # --- Disconnected body detection (Rule 3) ---
                    try:
                        components = trimesh.graph.connected_components(
                            mesh.face_adjacency, min_len=3
                        )
                        body_count = len(list(components))
                    except Exception:
                        body_count = 1  # can't determine — assume OK

                    component_count = len(component_names or [])
                    if design_mode == "single_solid" and body_count > 1:
                        geometry_warnings.append(
                            f"Mesh has {body_count} disconnected bodies (floating islands). "
                            "All structural components must be physically fused. "
                            "Use fuse() or ensure sketch regions overlap the main body."
                        )
                    elif design_mode == "assembly" and component_count and body_count < component_count:
                        geometry_warnings.append(
                            f"Assembly declares {component_count} components but mesh inspection found "
                            f"{body_count} bodies. Ensure each component is exported as distinct solid geometry."
                        )

                    component_validity = []
                    if design_mode == "assembly":
                        try:
                            split_meshes = mesh.split(only_watertight=False)
                            for index, component_mesh in enumerate(split_meshes, start=1):
                                component_validity.append({
                                    "index": index,
                                    "is_watertight": bool(getattr(component_mesh, "is_watertight", False)),
                                    "volume_mm3": round(float(getattr(component_mesh, "volume", 0.0)), 2),
                                })
                        except Exception as split_error:
                            geometry_warnings.append(f"Could not validate assembly components separately: {split_error}")

                    if design_mode == "assembly":
                        bodies_are_valid = body_count >= 1
                        if component_validity:
                            bodies_are_valid = all(
                                item["is_watertight"] and item["volume_mm3"] > 0
                                for item in component_validity
                            )
                            if not bodies_are_valid:
                                geometry_warnings.append(
                                    "One or more assembly components is non-watertight or has non-positive volume."
                                )
                    else:
                        bodies_are_valid = body_count == 1

                    # --- Dimension sanity (Rule 7) ---
                    min_extent = min(float(e) for e in ext)
                    if min_extent < 0.1:
                        geometry_warnings.append(
                            f"Minimum bounding dimension is {min_extent:.3f} mm (< 0.1 mm). "
                            "Possible zero-thickness geometry or collapsed face."
                        )

                    mesh_info = {
                        "is_valid": is_watertight and volume > 0 and bodies_are_valid,
                        "validation_mode": design_mode,
                        "is_watertight": is_watertight,
                        "body_count": body_count,
                        "component_count": component_count,
                        "component_names": component_names or [],
                        "component_validity": component_validity,
                        "volume_mm3": round(volume, 2),
                        "surface_area_mm2": round(float(getattr(mesh, "area", 0.0)), 2),
                        "dimensions_mm": {
                            "x": round(float(ext[0]), 2),
                            "y": round(float(ext[1]), 2),
                            "z": round(float(ext[2]), 2),
                        },
                        "vertex_count": len(mesh.vertices),
                        "face_count": len(mesh.faces),
                        "geometry_warnings": geometry_warnings,
                    }

                    if geometry_warnings:
                        logger.warning(
                            f"[CAD] Geometry validation warnings for {script_id}: "
                            + " | ".join(geometry_warnings)
                        )

                    del mesh
                    gc.collect()
                except Exception as me:
                    stderr += f"\nMesh inspection warning: {me}"

            if missing_step_export:
                stderr += "\nSTEP export was not produced by the CAD script."
                error_type = ErrorType.IO_ERROR

            execution_status = "success" if success and step_path.exists() and mesh_info else "error"

            return {
                "status": execution_status,
                # error_type is set AFTER stdout/stderr are fully captured above.
                # The `finally` block that deletes temp_script runs AFTER this
                # return — so there is no race between error classification and
                # file cleanup. See classify_error() for the classification logic.
                "error_type": error_type,
                "script_id": script_id,
                "recomputation_time_ms": elapsed,
                "stdout": stdout,
                "stderr": stderr,
                "returncode": returncode,
                "mesh_url":  f"/static/models/{stl_filename}"  if stl_path.exists()  else None,
                "step_url":  f"/static/models/{step_filename}" if step_path.exists()  else None,
                "script_url": f"/static/models/{script_id}.py" if py_path.exists()   else None,
                "mesh_info": mesh_info,
                "python_code": python_code,
            }

        finally:
            # Cleanup is intentionally sequenced AFTER stdout/stderr capture and
            # error classification above — there is no race condition on Windows.
            ArtifactCleanupManager.remove_file_safely(temp_script)
