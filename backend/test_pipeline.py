import sys
import asyncio
import time
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent))

from services.cad_runner import CADRunner
from services.cleanup import ArtifactCleanupManager
from config import MODELS_DIR

async def run_week2_async_tests():
    print("=" * 60)
    print("[TEST] RUNNING WEEK 2 ASYNC SUBPROCESS & ERROR TRAPPING TESTS")
    print("=" * 60)

    # 1. Test Asynchronous Subprocess Execution
    test_script_id = "async_part_w2"
    sample_cad_code = """PARAMS = {
    "bracket_length": 50.0,
    "width": 30.0,
    "height": 15.0
}

from build123d import *

with BuildPart() as part:
    Box(PARAMS["bracket_length"], PARAMS["width"], PARAMS["height"])

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
print(f"Executed async mesh: {PARAMS['bracket_length']}x{PARAMS['width']}x{PARAMS['height']}")
"""

    print("\n[1/4] Testing Async Execution Subprocess...")
    res = await CADRunner.execute_script_async(
        script_id=test_script_id,
        python_code=sample_cad_code
    )

    assert res["status"] == "success", f"Async execution failed: {res.get('stderr')}"
    assert res["mesh_url"] is not None, "Mesh URL should be present"
    print(f"[OK] Executed in {res['recomputation_time_ms']} ms")
    print(f"     Mesh URL: {res['mesh_url']}")
    print(f"     Mesh Info: {res.get('mesh_info')}")

    # 2. Test Error Trapping & Traceback Extraction (Self-Correction readiness)
    print("\n[2/4] Testing Subprocess Error Trapping & Traceback Capture...")
    broken_code = """PARAMS = {
    "length": 40.0
}

from build123d import *

# Intentional Logic Exception
x = 10 / 0  # ZeroDivisionError
"""

    error_res = await CADRunner.execute_script_async(
        script_id="broken_part_test",
        python_code=broken_code
    )

    assert error_res["status"] == "error", "Broken code should return status 'error'"
    assert "ZeroDivisionError" in error_res["stderr"], "Stderr must contain ZeroDivisionError traceback"
    print("[OK] Error Trapped Successfully:")
    print(f"     Return Code: {error_res['returncode']}")
    print(f"     Captured Traceback Snippet: {error_res['stderr'].strip().splitlines()[-1]}")

    # 3. Test Concurrent Async Executions
    print("\n[3/4] Testing Concurrent Non-Blocking Execution Pool (3 Parallel Jobs)...")
    tasks = [
        CADRunner.execute_script_async(
            script_id=f"parallel_{i}",
            python_code=sample_cad_code,
            parameters={"bracket_length": 40 + i * 10, "width": 20.0, "height": 10.0}
        )
        for i in range(3)
    ]

    start_conc = time.time()
    results = await asyncio.gather(*tasks)
    total_conc_ms = int((time.time() - start_conc) * 1000)

    for idx, r in enumerate(results):
        assert r["status"] == "success", f"Parallel execution {idx} failed: {r.get('stderr', '')[:200]}"
    print(f"[OK] 3 Concurrent CAD Executions completed in total {total_conc_ms} ms")

    # 4. Test Artifact Cleanup
    print("\n[4/4] Testing Artifact Cleanup Manager...")
    cleaned_files = ArtifactCleanupManager.cleanup_old_artifacts(max_age_seconds=0)
    print(f"[OK] Cleanup executed successfully. Removed {cleaned_files} artifacts.")

    print("\n" + "=" * 60)
    print("[SUCCESS] ALL WEEK 2 PIPELINE TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_week2_async_tests())
