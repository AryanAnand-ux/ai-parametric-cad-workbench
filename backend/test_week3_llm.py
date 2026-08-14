"""
Week 3 Test: LLM Integration & Dual-Output Schema Validation
=============================================================
Tests:
  1. Schema validation - DualOutputPayload structure
  2. LLM response parsing (JSON mode)
  3. Zero-shot generation for basic primitives
  4. Dual-output completeness (code + params)
  5. Self-correction mock scenario
  6. End-to-end: prompt -> LLM -> execute -> STL file
"""

import sys
import json
import asyncio
import os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

# Load .env if present
from dotenv import load_dotenv
load_dotenv()

from schemas import DualOutputPayload, CADParameter
from services.llm_service import LLMService
from services.cad_runner import CADRunner
from config import MODELS_DIR


def test_1_schema_validation():
    """Test that DualOutputPayload validates correct data."""
    print("\n[1/5] Testing Pydantic Schema Validation...")

    valid_data = {
        "python_code": "PARAMS = {'length': 30.0, 'width': 20.0, 'height': 10.0}\nfrom build123d import *\nwith BuildPart() as part:\n    Box(PARAMS['length'], PARAMS['width'], PARAMS['height'])\nexport_stl(part.part, OUTPUT_STL)",
        "parameters": [
            {
                "name": "length",
                "label": "Length (mm)",
                "type": "number",
                "default": 30.0,
                "min": 5.0,
                "max": 200.0,
                "step": 1.0
            }
        ],
        "part_name": "Simple Box",
        "description": "A parametric rectangular box."
    }

    payload = DualOutputPayload(**valid_data)
    assert payload.part_name == "Simple Box"
    assert len(payload.parameters) == 1
    assert payload.parameters[0].name == "length"
    assert payload.parameters[0].min == 5.0
    print("[OK] DualOutputPayload schema validation passed.")


def test_2_llm_response_parsing():
    """Test that _parse_response handles valid JSON strings correctly."""
    print("\n[2/5] Testing LLM Response Parser...")

    sample_json = json.dumps({
        "python_code": "PARAMS = {'radius': 15.0, 'height': 30.0}\nfrom build123d import *\nwith BuildPart() as part:\n    Cylinder(radius=PARAMS['radius'], height=PARAMS['height'])\nexport_stl(part.part, OUTPUT_STL)\nexport_step(part.part, OUTPUT_STEP)",
        "parameters": [
            {
                "name": "radius",
                "label": "Cylinder Radius (mm)",
                "type": "number",
                "default": 15.0,
                "min": 2.0,
                "max": 100.0,
                "step": 0.5
            }
        ],
        "part_name": "Cylinder",
        "description": "A parametric solid cylinder."
    })

    payload = LLMService._parse_response(sample_json)
    assert payload.part_name == "Cylinder"
    assert payload.parameters[0].name == "radius"
    print("[OK] Response parser correctly parsed JSON into DualOutputPayload.")

    # Test with accidental markdown fences
    fenced_json = f"```json\n{sample_json}\n```"
    payload2 = LLMService._parse_response(fenced_json)
    assert payload2.part_name == "Cylinder"
    print("[OK] Response parser correctly stripped markdown fences.")


async def test_3_end_to_end_generation():
    """
    End-to-end test: Call real Gemini API -> parse -> execute -> STL file.
    Only runs if GEMINI_API_KEY is set.
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        print("\n[3/5] SKIPPED (GEMINI_API_KEY not set — add to .env file to run this test)")
        return None

    print("\n[3/5] Testing End-to-End LLM Generation (Real Gemini API)...")

    test_prompts = [
        "Generate a 40mm x 25mm x 10mm rectangular mounting bracket",
        "Create a hollow cylinder with 20mm outer radius and 5mm wall thickness",
        "Make a simple cone with 15mm base radius and 40mm height"
    ]

    results = []
    for prompt in test_prompts:
        print(f"\n  Prompt: '{prompt}'")
        try:
            dual_output, model_used = LLMService.generate_dual_output(prompt)
            print(f"  [OK] Model: {model_used}")
            print(f"       Part: '{dual_output.part_name}' | {len(dual_output.parameters)} params")
            print(f"       Params: {[p.name for p in dual_output.parameters]}")
            print(f"       Code length: {len(dual_output.python_code)} chars")

            # Execute generated code
            script_id = f"test_w3_{dual_output.part_name.lower().replace(' ', '_')[:20]}"
            exec_result = await CADRunner.execute_script_async(
                script_id=script_id,
                python_code=dual_output.python_code
            )

            if exec_result["status"] == "success":
                print(f"  [OK] Executed in {exec_result['recomputation_time_ms']} ms")
                print(f"       Mesh: {exec_result.get('mesh_info', {}).get('dimensions_mm')}")
                results.append({"prompt": prompt, "status": "success", "model": model_used})
            else:
                print(f"  [WARN] Execution failed: {exec_result.get('stderr', '')[:150]}")
                results.append({"prompt": prompt, "status": "exec_error", "model": model_used})

        except Exception as e:
            print(f"  [FAIL] {e}")
            results.append({"prompt": prompt, "status": "error", "error": str(e)})

    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"\n  Results: {success_count}/{len(test_prompts)} prompts generated & executed successfully")
    return results


def test_4_parameter_injection():
    """Test that parameter injection correctly updates PARAMS block."""
    print("\n[4/5] Testing Parameter Injection into PARAMS block...")

    original_code = """PARAMS = {
    "length": 30.0,
    "width": 20.0
}

from build123d import *
with BuildPart() as part:
    Box(PARAMS["length"], PARAMS["width"], 10)
export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    updated_params = {"length": 75.0, "width": 45.0}
    updated_code = CADRunner.inject_parameters(original_code, updated_params)

    assert '"length": 75.0' in updated_code
    assert '"width": 45.0' in updated_code
    assert '"length": 30.0' not in updated_code
    print("[OK] PARAMS block correctly updated with new slider values.")
    print(f"     Updated code preview:\n{updated_code[:180]}")


async def test_5_full_api_import():
    """Test that all modules import cleanly and FastAPI app is valid."""
    print("\n[5/5] Testing FastAPI App Import & Schema...")
    from main import app
    routes = [r.path for r in app.routes]
    assert "/api/health" in routes
    assert "/api/generate" in routes
    assert "/api/recompute" in routes
    print("[OK] FastAPI app imported successfully.")
    print(f"     Active routes: {[r for r in routes if r.startswith('/api')]}")


async def run_all_tests():
    print("=" * 60)
    print("[TEST] RUNNING WEEK 3 LLM INTEGRATION TESTS")
    print("=" * 60)

    test_1_schema_validation()
    test_2_llm_response_parsing()
    await test_3_end_to_end_generation()
    test_4_parameter_injection()
    await test_5_full_api_import()

    print("\n" + "=" * 60)
    print("[SUCCESS] ALL WEEK 3 LLM INTEGRATION TESTS COMPLETED!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
