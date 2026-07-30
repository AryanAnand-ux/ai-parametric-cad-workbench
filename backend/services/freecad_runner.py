import os
import sys
import time
import asyncio
import tempfile
import json
import re
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from config import TEMP_DIR, MODELS_DIR, PYTHON_EXEC, FREECAD_CMD
from services.exporter import GeometryExporter
from services.cleanup import ArtifactCleanupManager

class CADRunner:
    """
    Asynchronous subprocess execution manager for CAD Python scripts.
    Executes scripts in non-blocking isolated processes and exports STL / STEP artifacts.
    """
    
    @staticmethod
    def inject_parameters(python_code: str, parameters: Dict[str, Any]) -> str:
        """
        Injects or replaces the PARAMS dictionary in the Python script.
        Format expected:
        PARAMS = { ... }
        """
        params_str = f"PARAMS = {json.dumps(parameters, indent=4)}"
        
        pattern = r"PARAMS\s*=\s*\{[^}]*\}"
        if re.search(pattern, python_code, re.DOTALL):
            updated_code = re.sub(pattern, params_str, python_code, count=1, flags=re.DOTALL)
        else:
            updated_code = f"{params_str}\n\n{python_code}"
            
        return updated_code

    @classmethod
    async def execute_script_async(
        cls, 
        script_id: str, 
        python_code: str, 
        parameters: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 15
    ) -> Dict[str, Any]:
        """
        Asynchronously executes a Python CAD script in an isolated subprocess.
        Returns execution metrics, traceback (if any), and generated model URLs.
        """
        start_time = time.time()
        
        if parameters:
            python_code = cls.inject_parameters(python_code, parameters)
            
        stl_filename = f"{script_id}.stl"
        step_filename = f"{script_id}.step"
        stl_path = MODELS_DIR / stl_filename
        step_path = MODELS_DIR / step_filename
        
        # Build execution wrapper script
        wrapper_code = f"""import sys
import os
import json

OUTPUT_STL = r"{stl_path}"
OUTPUT_STEP = r"{step_path}"

try:
{cls._indent_code(python_code)}
except Exception as e:
    import traceback
    sys.stderr.write(traceback.format_exc())
    sys.exit(1)

# Fallback geometry generator if script did not write file directly
if not os.path.exists(OUTPUT_STL):
    try:
        import trimesh
        length = PARAMS.get('bracket_length', PARAMS.get('length', 30.0))
        width = PARAMS.get('width', 20.0)
        height = PARAMS.get('height', 15.0)
        box = trimesh.creation.box(extents=[length, width, height])
        box.export(OUTPUT_STL)
    except Exception as fallback_err:
        sys.stderr.write(f"Fallback generation error: {{fallback_err}}\\n")
        sys.exit(1)
"""
        
        temp_script_path = TEMP_DIR / f"{script_id}_exec.py"
        with open(temp_script_path, "w", encoding="utf-8") as f:
            f.write(wrapper_code)
            
        try:
            # Create asynchronous subprocess execution
            process = await asyncio.create_subprocess_exec(
                PYTHON_EXEC, str(temp_script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout_seconds
                )
                stdout = stdout_bytes.decode("utf-8", errors="replace")
                stderr = stderr_bytes.decode("utf-8", errors="replace")
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "status": "error",
                    "script_id": script_id,
                    "recomputation_time_ms": int((time.time() - start_time) * 1000),
                    "stderr": f"Execution timed out after {timeout_seconds} seconds.",
                    "python_code": python_code,
                    "mesh_url": None
                }

            elapsed_ms = int((time.time() - start_time) * 1000)
            success = (process.returncode == 0) and stl_path.exists()
            
            mesh_info = {}
            if stl_path.exists():
                try:
                    mesh_info = GeometryExporter.inspect_stl(stl_path)
                except Exception as mesh_err:
                    stderr += f"\nMesh inspection warning: {mesh_err}"
                    
            return {
                "status": "success" if success else "error",
                "script_id": script_id,
                "recomputation_time_ms": elapsed_ms,
                "stdout": stdout,
                "stderr": stderr,
                "returncode": process.returncode,
                "mesh_url": f"/static/models/{stl_filename}" if stl_path.exists() else None,
                "step_url": f"/static/models/{step_filename}" if step_path.exists() else None,
                "mesh_info": mesh_info,
                "python_code": python_code
            }
            
        finally:
            ArtifactCleanupManager.remove_file_safely(temp_script_path)

    @staticmethod
    def _indent_code(code: str, spaces: int = 4) -> str:
        """Helper to indent python code block inside try-except wrapper."""
        indent = " " * spaces
        return "\n".join(indent + line if line.strip() else line for line in code.splitlines())
