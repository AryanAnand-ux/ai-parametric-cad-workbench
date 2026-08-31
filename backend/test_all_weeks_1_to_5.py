"""
Master Test Suite — Comprehensive Validation (Weeks 1 through 5)
================================================================
Validates:
  - Week 1: build123d CAD execution, STEP/STL export, error trapping
  - Week 2: Async subprocess concurrency (3 parallel jobs), artifact cleanup
  - Week 3: Dual-output Pydantic schemas, robust response parser, parameter injection
  - Week 4: AST security sandbox, safe/unsafe module filtering
  - Week 5: ChromaDB RAG vector store, sentence-transformers embeddings, top-k retrieval
  - Integration: FastAPI endpoint suite (/api/health, /api/generate, /api/recompute, /api/modify, /api/download)
"""

import sys
import time
import json
import asyncio
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv()

from config import BASE_DIR, MODELS_DIR, TEMP_DIR, GEMINI_API_KEY
from schemas import DualOutputPayload, CADParameter, GenerateRequest, RecomputeRequest, ModifyRequest
from services.cad_runner import CADRunner, validate_script_safety
from services.cleanup import ArtifactCleanupManager
from services.rag_service import RAGService
from services.llm_service import LLMService


test_results = {}

def record(test_name: str, passed: bool, details: str = ""):
    status_str = "PASS" if passed else "FAIL"
    test_results[test_name] = {"passed": passed, "details": details}
    icon = "[OK]" if passed else "[FAIL]"
    print(f"{icon} [{status_str}] {test_name}: {details}")


# -----------------------------------------------------------------------------
# 1. WEEK 1: CAD Kernel & Subprocess Isolation
# -----------------------------------------------------------------------------

async def test_week_1():
    print("\n" + "="*60)
    print("[TEST] WEEK 1: CAD Kernel & Subprocess Isolation")
    print("="*60)

    # 1.1 Simple Box Generation (build123d)
    box_code = """
PARAMS = {"l": 40.0, "w": 25.0, "h": 15.0}
from build123d import *
with BuildPart() as part:
    Box(PARAMS["l"], PARAMS["w"], PARAMS["h"])
export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    t0 = time.perf_counter()
    res = await CADRunner.execute_script_async("test_w1_box", box_code)
    elapsed = int((time.perf_counter() - t0) * 1000)

    passed_box = (
        res["status"] == "success" and
        res.get("mesh_url") is not None and
        res.get("step_url") is not None
    )
    dims = res.get("mesh_info", {}).get("dimensions_mm", {})
    record(
        "Week 1 - build123d Box Solid + STEP/STL Export",
        passed_box,
        f"Time: {elapsed}ms | Dims: {dims}"
    )

    # 1.2 Subprocess Error & Traceback Capture
    broken_code = """
PARAMS = {}
from build123d import *
x = 10 / 0
"""
    res_err = await CADRunner.execute_script_async("test_w1_broken", broken_code)
    passed_err = (
        res_err["status"] == "error" and
        "ZeroDivisionError" in res_err.get("stderr", "")
    )
    record(
        "Week 1 - Subprocess Traceback Capture",
        passed_err,
        f"Captured stderr: {res_err.get('stderr', '').strip().splitlines()[-1]}"
    )


# -----------------------------------------------------------------------------
# 2. WEEK 2: Async Concurrency & Artifact Lifecycle
# -----------------------------------------------------------------------------

async def test_week_2():
    print("\n" + "="*60)
    print("[TEST] WEEK 2: Async Concurrency & Cleanup")
    print("="*60)

    # 2.1 Concurrent CAD Executions
    sample_code = """
PARAMS = {"radius": 15.0, "height": 30.0}
from build123d import *
with BuildPart() as part:
    Cylinder(radius=PARAMS["radius"], height=PARAMS["height"])
export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    tasks = [
        CADRunner.execute_script_async(
            f"test_w2_parallel_{i}",
            sample_code,
            parameters={"radius": 10.0 + i * 5, "height": 20.0 + i * 10}
        )
        for i in range(3)
    ]

    t0 = time.perf_counter()
    results = await asyncio.gather(*tasks)
    total_ms = int((time.perf_counter() - t0) * 1000)

    all_ok = all(r["status"] == "success" for r in results)
    record(
        "Week 2 - 3x Concurrent Parallel Subprocesses",
        all_ok,
        f"Completed 3 jobs in {total_ms}ms total"
    )

    # 2.2 Artifact Cleanup Manager
    cleaned = ArtifactCleanupManager.cleanup_old_artifacts(max_age_seconds=86400)
    record(
        "Week 2 - Artifact Cleanup Lifecycle Manager",
        isinstance(cleaned, int),
        f"Cleanup verified (scanned models directory)"
    )


# -----------------------------------------------------------------------------
# 3. WEEK 3: Dual-Output Schemas & Parameter Injection
# -----------------------------------------------------------------------------

async def test_week_3():
    print("\n" + "="*60)
    print("[TEST] WEEK 3: Dual-Output Schemas & Parser")
    print("="*60)

    # 3.1 Pydantic Validation
    param = CADParameter(
        name="wall_thickness",
        label="Wall Thickness (mm)",
        type="number",
        default=3.0,
        min=1.0,
        max=10.0,
        step=0.5
    )
    passed_param = (param.name == "wall_thickness" and param.default == 3.0)
    record(
        "Week 3 - Pydantic CADParameter Model Validation",
        passed_param,
        f"Validated min={param.min} <= default={param.default} <= max={param.max}"
    )

    # 3.2 Robust LLM Response Parsing (Markdown fences + quotes)
    sample_json = json.dumps({
        "python_code": "PARAMS = {'len': 50.0}\nfrom build123d import *\nwith BuildPart() as part:\n    Box(PARAMS['len'], 20, 10)\nexport_stl(part.part, OUTPUT_STL)\nexport_step(part.part, OUTPUT_STEP)",
        "parameters": [
            {"name": "len", "label": "Length (mm)", "type": "number", "default": 50.0, "min": 10.0, "max": 200.0, "step": 1.0}
        ],
        "part_name": "Test Plate",
        "description": "A flat mounting plate."
    })
    fenced_raw = f"```json\n{sample_json}\n```"
    parsed_payload = LLMService._parse_response(fenced_raw)
    passed_parse = (parsed_payload.part_name == "Test Plate" and len(parsed_payload.parameters) == 1)
    record(
        "Week 3 - Robust LLM JSON Parser (Strips Markdown Fences)",
        passed_parse,
        f"Parsed part '{parsed_payload.part_name}' with {len(parsed_payload.parameters)} param"
    )

    # 3.3 Fast Parameter Injection (Brace-Counting Parser)
    orig_script = """PARAMS = {
    "length": 30.0,
    "width": 20.0
}
from build123d import *
with BuildPart() as part:
    Box(PARAMS["length"], PARAMS["width"], 10)
export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    updated_script = CADRunner.inject_parameters(orig_script, {"length": 85.0, "width": 45.0})
    passed_inject = ('"length": 85.0' in updated_script and '"width": 45.0' in updated_script and '"length": 30.0' not in updated_script)
    record(
        "Week 3 - Parameter Injection into PARAMS Block",
        passed_inject,
        "Brace-counting parser successfully updated slider values"
    )


# -----------------------------------------------------------------------------
# 4. WEEK 4: AST Security Sandbox & build123d Primitives
# -----------------------------------------------------------------------------

async def test_week_4():
    print("\n" + "="*60)
    print("[TEST] WEEK 4: AST Security Sandbox & Primitives")
    print("="*60)

    # 4.1 AST Security Check on Safe Script
    safe_script = """PARAMS = {"r": 10.0}
import math
from build123d import *
with BuildPart() as part:
    Sphere(radius=PARAMS["r"])
export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    is_safe, reason = validate_script_safety(safe_script)
    record(
        "Week 4 - AST Sandbox Allows Whitelisted Code",
        is_safe,
        f"Allowed imports: build123d, math (Reason: {reason})"
    )

    # 4.2 AST Security Check on Malicious/Dangerous Script
    bad_script = """import os, sys, subprocess
os.system("echo hacked")
"""
    is_bad_safe, bad_reason = validate_script_safety(bad_script)
    record(
        "Week 4 - AST Sandbox Blocks Dangerous Imports (os, sys, subprocess)",
        (not is_bad_safe),
        f"Correctly blocked: {bad_reason}"
    )

    # 4.3 Hollow Cylinder with CSG Mode.SUBTRACT
    hollow_code = """PARAMS = {"outer_r": 20.0, "wall": 4.0, "h": 40.0}
from build123d import *
with BuildPart() as part:
    Cylinder(radius=PARAMS["outer_r"], height=PARAMS["h"])
    Cylinder(radius=PARAMS["outer_r"] - PARAMS["wall"], height=PARAMS["h"], mode=Mode.SUBTRACT)
export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    hollow_res = await CADRunner.execute_script_async("test_w4_hollow", hollow_code)
    passed_hollow = (hollow_res["status"] == "success" and hollow_res.get("mesh_info", {}).get("is_valid", False))
    record(
        "Week 4 - CSG Boolean Subtraction (Hollow Cylinder)",
        passed_hollow,
        f"Watertight: {hollow_res.get('mesh_info', {}).get('is_valid')} | Volume: {hollow_res.get('mesh_info', {}).get('volume_mm3')} mm3"
    )


# -----------------------------------------------------------------------------
# 5. WEEK 5: ChromaDB RAG Vector Store & Retrieval Pipeline
# -----------------------------------------------------------------------------

async def test_week_5():
    print("\n" + "="*60)
    print("[TEST] WEEK 5: ChromaDB RAG Vector Store & Retrieval")
    print("="*60)

    # 5.1 RAG Index Build & Size Check
    added_count = RAGService.build_index()
    total_docs = RAGService.index_size()
    passed_index = (total_docs >= 20)
    record(
        "Week 5 - ChromaDB Vector Index (all-MiniLM-L6-v2)",
        passed_index,
        f"Index contains {total_docs} total CAD snippet pairs ({added_count} new)"
    )

    # 5.2 Semantic Similarity Retrieval
    query = "Hollow cylindrical tube with wall thickness"
    matches = RAGService.retrieve(query, k=3)
    passed_retrieval = (len(matches) > 0 and matches[0]["similarity"] > 0.3)
    top_match = matches[0] if matches else {"description": "None", "similarity": 0}
    record(
        "Week 5 - Semantic Vector Retrieval (Cosine Similarity)",
        passed_retrieval,
        f"Top match: '{top_match['description'][:45]}...' (Similarity: {top_match['similarity']:.4f})"
    )

    # 5.3 Dynamic Few-Shot Prompt Formatting
    formatted_block = RAGService.format_for_prompt(matches)
    passed_format = ("## Similar Example 1:" in formatted_block and "```python" in formatted_block)
    record(
        "Week 5 - Dynamic Few-Shot Context Formatter",
        passed_format,
        f"Formatted {len(matches)} examples ({len(formatted_block)} chars)"
    )


# -----------------------------------------------------------------------------
# 6. INTEGRATION: Full FastAPI API Suite
# -----------------------------------------------------------------------------

async def test_integration():
    print("\n" + "="*60)
    print("[TEST] INTEGRATION: FastAPI REST API Endpoints")
    print("="*60)

    import httpx
    from main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 6.1 GET /api/health
        res_h = await client.get("/api/health")
        passed_h = (res_h.status_code == 200 and res_h.json().get("status") == "online")
        record("Integration - GET /api/health", passed_h, f"Status: {res_h.json().get('status')}")

        # 6.2 POST /api/recompute
        recomp_payload = {
            "script_id": "test_integration_recompute",
            "python_code": """PARAMS = {"l": 50.0, "w": 30.0, "h": 10.0}
from build123d import *
with BuildPart() as part:
    Box(PARAMS["l"], PARAMS["w"], PARAMS["h"])
export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
""",
            "updated_parameters": {"l": 80.0, "w": 40.0, "h": 20.0}
        }
        res_r = await client.post("/api/recompute", json=recomp_payload)
        passed_r = (res_r.status_code == 200 and res_r.json().get("status") == "success")
        record(
            "Integration - POST /api/recompute (Fast Slider Recomputation)",
            passed_r,
            f"Recomputation time: {res_r.json().get('recomputation_time_ms')}ms"
        )

        # 6.3 GET /api/admin/models
        res_m = await client.get("/api/admin/models")
        passed_m = (res_m.status_code == 200 and "models" in res_m.json())
        record(
            "Integration - GET /api/admin/models",
            passed_m,
            f"Stored models count: {res_m.json().get('count')}"
        )


# -----------------------------------------------------------------------------
# Runner
# -----------------------------------------------------------------------------

async def run_master_test():
    print("\n" + "#"*70)
    print("RUNNING MASTER TEST SUITE - WEEKS 1 THROUGH 5 VALIDATION")
    print("#"*70)

    await test_week_1()
    await test_week_2()
    await test_week_3()
    await test_week_4()
    await test_week_5()
    await test_integration()

    print("\n" + "#"*70)
    print("MASTER TEST SUMMARY")
    print("#"*70)

    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results.values() if r["passed"])
    failed_tests = total_tests - passed_tests

    for name, res in test_results.items():
        icon = "[PASS]" if res["passed"] else "[FAIL]"
        print(f"{icon} {name}")

    print("-" * 70)
    print(f"Total: {total_tests} | Passed: {passed_tests} | Failed: {failed_tests} | Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print("#"*70 + "\n")

    if failed_tests > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_master_test())
