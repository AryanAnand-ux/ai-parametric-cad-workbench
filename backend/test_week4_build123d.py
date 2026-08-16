"""
Week 4 Test — build123d + RAG Pipeline
======================================
Tests:
  1. build123d import and basic geometry creation
  2. STEP + STL export from build123d
  3. AST security sandbox (blocks bad imports)
  4. Parameter injection into PARAMS block
  5. Async CAD subprocess execution (cad_runner.py)
  6. RAG service: ChromaDB index + retrieval
"""
import sys
import asyncio
import os
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv()

from services.cad_runner import CADRunner, validate_script_safety



SIMPLE_BOX_SCRIPT = '''
PARAMS = {"length": 40.0, "width": 25.0, "height": 15.0}
from build123d import *

with BuildPart() as part:
    Box(PARAMS["length"], PARAMS["width"], PARAMS["height"])

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''

HOLLOW_CYL_SCRIPT = '''
PARAMS = {"outer_radius": 20.0, "wall_thickness": 3.0, "height": 50.0}
from build123d import *

outer = PARAMS["outer_radius"]
inner = outer - PARAMS["wall_thickness"]

with BuildPart() as part:
    Cylinder(radius=outer, height=PARAMS["height"])
    Cylinder(radius=inner, height=PARAMS["height"], mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''

UNSAFE_SCRIPT = '''
import os
import sys
PARAMS = {}
from build123d import *
with BuildPart() as part:
    Box(10,10,10)
export_stl(part.part, OUTPUT_STL)
'''


@pytest.mark.asyncio
async def test_1_build123d_import():
    print("\n[1/6] Testing build123d Import...")
    try:
        from build123d import BuildPart, Box, Cylinder, Mode
        print("[OK] build123d imports successfully.")
    except ImportError as e:
        print(f"[FAIL] build123d import failed: {e}")
        sys.exit(1)


@pytest.mark.asyncio
async def test_2_ast_sandbox():
    print("\n[2/6] Testing AST Security Sandbox...")

    safe, msg = validate_script_safety(SIMPLE_BOX_SCRIPT)
    assert safe, f"Safe script rejected: {msg}"
    print(f"[OK] Safe script accepted: {msg}")

    safe, msg = validate_script_safety(UNSAFE_SCRIPT)
    assert not safe, "Unsafe script should have been blocked!"
    print(f"[OK] Unsafe script blocked: {msg}")


@pytest.mark.asyncio
async def test_3_param_injection():
    print("\n[3/6] Testing Parameter Injection...")
    updated = CADRunner.inject_parameters(
        SIMPLE_BOX_SCRIPT,
        {"length": 80.0, "width": 50.0, "height": 30.0}
    )
    assert '"length": 80.0' in updated
    assert '"width": 50.0' in updated
    assert '"length": 40.0' not in updated
    print("[OK] PARAMS block correctly updated.")


@pytest.mark.asyncio
async def test_4_box_execution():
    print("\n[4/6] Testing build123d Box Execution...")
    result = await CADRunner.execute_script_async(
        script_id="test_w4_box",
        python_code=SIMPLE_BOX_SCRIPT
    )
    if result["status"] == "success":
        print(f"[OK] Box executed in {result['recomputation_time_ms']} ms")
        print(f"     STL: {result['mesh_url']}")
        print(f"     STEP: {result['step_url']}")
        print(f"     Mesh: {result.get('mesh_info', {}).get('dimensions_mm')}")
    else:
        print(f"[FAIL] Execution failed:\n{result['stderr'][:400]}")


@pytest.mark.asyncio
async def test_5_hollow_cylinder():
    print("\n[5/6] Testing Hollow Cylinder (Mode.SUBTRACT)...")
    result = await CADRunner.execute_script_async(
        script_id="test_w4_hollow",
        python_code=HOLLOW_CYL_SCRIPT
    )
    if result["status"] == "success":
        print(f"[OK] Hollow cylinder in {result['recomputation_time_ms']} ms")
        print(f"     Mesh dims: {result.get('mesh_info', {}).get('dimensions_mm')}")
    else:
        print(f"[FAIL] {result['stderr'][:300]}")


@pytest.mark.asyncio
async def test_6_rag_index():
    print("\n[6/6] Testing RAG ChromaDB Index (local sentence-transformers)...")
    from services.rag_service import RAGService

    print("  Building index from 20 examples (downloads model on first run ~90MB)...")
    count = RAGService.build_index()
    total = RAGService.index_size()
    print(f"[OK] Index built: {count} new docs added, {total} total in ChromaDB")

    results = RAGService.retrieve("hollow cylinder with wall thickness", k=3)
    print(f"[OK] Retrieved {len(results)} examples:")
    for r in results:
        print(f"     sim={r['similarity']:.3f} -> {r['description'][:60]}")


async def run_all():
    print("=" * 60)
    print("[TEST] WEEK 4 — BUILD123D + RAG PIPELINE TESTS")
    print("=" * 60)

    await test_1_build123d_import()
    await test_2_ast_sandbox()
    await test_3_param_injection()
    await test_4_box_execution()
    await test_5_hollow_cylinder()
    await test_6_rag_index()

    print("\n" + "=" * 60)
    print("[DONE] ALL WEEK 4 TESTS COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all())
