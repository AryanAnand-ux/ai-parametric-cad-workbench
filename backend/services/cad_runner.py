"""
CAD Runner — build123d Subprocess Executor
==========================================
Replaces freecad_runner.py (trimesh).
Executes build123d Python scripts in isolated subprocesses.

Key responsibilities:
- Inject updated PARAMS into scripts for parametric recomputation
- Run scripts safely via asyncio.create_subprocess_exec (non-blocking)
- AST security sandbox: whitelist only build123d, math, typing imports
- Export STL (WebGL preview) + STEP (download) files
- Return execution metrics and file URLs
"""

import os
import re
import ast
import sys
import json
import time
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from config import TEMP_DIR, MODELS_DIR, PYTHON_EXEC
from services.cleanup import ArtifactCleanupManager

logger = logging.getLogger("cad_workbench.cad_runner")

# ---------------------------------------------------------------------------
# Allowed imports whitelist (AST security sandbox)
# ---------------------------------------------------------------------------

ALLOWED_IMPORTS = {
    "build123d", "math", "typing", "types",
    "collections", "itertools", "functools",
    "enum", "dataclasses", "abc", "operator"
}


# ---------------------------------------------------------------------------
# AST Security Sandbox
# ---------------------------------------------------------------------------

def validate_script_safety(python_code: str) -> tuple[bool, str]:
    """
    Parses the script with Python's AST module and verifies that only
    whitelisted libraries are imported. Blocks os, sys, subprocess, etc.

    Returns: (is_safe: bool, reason: str)
    """
    try:
        tree = ast.parse(python_code)
    except SyntaxError as e:
        return False, f"Syntax error: {e}"

    for node in ast.walk(tree):
        # Check `import X` statements
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in ALLOWED_IMPORTS:
                    return False, f"Blocked import: '{alias.name}' (not in whitelist)"

        # Check `from X import Y` statements
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                if root not in ALLOWED_IMPORTS:
                    return False, f"Blocked import: 'from {node.module}' (not in whitelist)"

    return True, "OK"


# ---------------------------------------------------------------------------
# Parameter Injection
# ---------------------------------------------------------------------------

def inject_parameters(python_code: str, parameters: Dict[str, Any]) -> str:
    """
    Replaces the PARAMS = {...} block with updated values.
    Uses re.DOTALL to correctly handle multi-line dicts.
    """
    params_str = f"PARAMS = {json.dumps(parameters, indent=4)}"
    pattern = r"PARAMS\s*=\s*\{.*?\}"
    if re.search(pattern, python_code, re.DOTALL):
        return re.sub(pattern, params_str, python_code, count=1, flags=re.DOTALL)
    return f"{params_str}\n\n{python_code}"


# ---------------------------------------------------------------------------
# Subprocess Wrapper Builder
# ---------------------------------------------------------------------------

def _build_wrapper(python_code: str, stl_posix: str, step_posix: str) -> str:
    """
    Wraps the user script with OUTPUT_STL / OUTPUT_STEP injection
    and a try/except that sends tracebacks to stderr.
    """
    indented = "\n".join(
        "    " + line if line.strip() else line
        for line in python_code.splitlines()
    )
    return f'''import sys, os
OUTPUT_STL  = r"{stl_posix}"
OUTPUT_STEP = r"{step_posix}"

try:
{indented}
except Exception:
    import traceback
    sys.stderr.write(traceback.format_exc())
    sys.exit(1)
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
        timeout_seconds: int = 30      # build123d needs more time than trimesh
    ) -> Dict[str, Any]:
        """
        Runs a build123d script in an isolated subprocess.
        Returns execution result dict with mesh_url, step_url, mesh_info.
        """
        start = time.time()

        if parameters:
            python_code = inject_parameters(python_code, parameters)

        # ── AST Security Check ────────────────────────────────────────────
        is_safe, reason = validate_script_safety(python_code)
        if not is_safe:
            logger.warning(f"[CAD] Script BLOCKED by AST sandbox: {reason}")
            return {
                "status": "error",
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
            step_path.as_posix()
        )

        temp_script = TEMP_DIR / f"{script_id}_exec.py"

        try:
            with open(temp_script, "w", encoding="utf-8") as f:
                f.write(wrapper)
        except OSError as e:
            return {
                "status": "error", "script_id": script_id,
                "recomputation_time_ms": 0,
                "stderr": f"Failed to write temp script: {e}",
                "mesh_url": None, "step_url": None, "mesh_info": {}
            }

        try:
            proc = await asyncio.create_subprocess_exec(
                PYTHON_EXEC, str(temp_script),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout_b, stderr_b = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return {
                    "status": "error", "script_id": script_id,
                    "recomputation_time_ms": int((time.time() - start) * 1000),
                    "stderr": f"Execution timed out after {timeout_seconds}s.",
                    "stdout": "", "returncode": -1,
                    "mesh_url": None, "step_url": None, "mesh_info": {}
                }

            stdout = stdout_b.decode("utf-8", errors="replace")
            stderr = stderr_b.decode("utf-8", errors="replace")
            elapsed = int((time.time() - start) * 1000)
            success = (proc.returncode == 0) and stl_path.exists()

            # ── Mesh inspection ───────────────────────────────────────────
            mesh_info = {}
            if stl_path.exists():
                try:
                    import trimesh
                    mesh = trimesh.load_mesh(str(stl_path))
                    ext = mesh.extents
                    mesh_info = {
                        "is_valid": mesh.is_watertight,
                        "volume_mm3": round(float(mesh.volume), 2),
                        "surface_area_mm2": round(float(mesh.area), 2),
                        "dimensions_mm": {
                            "x": round(float(ext[0]), 2),
                            "y": round(float(ext[1]), 2),
                            "z": round(float(ext[2]), 2),
                        },
                        "vertex_count": len(mesh.vertices),
                        "face_count": len(mesh.faces),
                    }
                except Exception as me:
                    stderr += f"\nMesh inspection warning: {me}"

            return {
                "status": "success" if success else "error",
                "script_id": script_id,
                "recomputation_time_ms": elapsed,
                "stdout": stdout,
                "stderr": stderr,
                "returncode": proc.returncode,
                "mesh_url":  f"/static/models/{stl_filename}"  if stl_path.exists()  else None,
                "step_url":  f"/static/models/{step_filename}" if step_path.exists()  else None,
                "mesh_info": mesh_info,
                "python_code": python_code,
            }

        finally:
            ArtifactCleanupManager.remove_file_safely(temp_script)
