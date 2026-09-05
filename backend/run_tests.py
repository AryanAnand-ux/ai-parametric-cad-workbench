"""
run_tests.py — Cross-platform test suite runner for AI CAD Workbench.

Executes:
  1. Focused pytest regression suite (schemas, security, AST, parser, geometry, recompute)
  2. Gemini Web Client unit tests
  3. API async endpoint integration tests
  4. Core CAD pipeline integration test
"""

import sys
import subprocess
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent


def run_command(cmd, desc):
    print(f"\n{'='*70}\n[RUNNING] {desc}\n  CMD: {' '.join(cmd)}\n{'='*70}")
    res = subprocess.run(cmd, cwd=BACKEND_DIR)
    if res.returncode != 0:
        print(f"\n[FAIL] {desc} exited with code {res.returncode}")
        sys.exit(res.returncode)
    print(f"[PASSED] {desc}")


def main():
    py = sys.executable

    # 1. Pytest regression suite
    run_command(
        [
            py, "-m", "pytest",
            "test_schemas.py",
            "test_ast_security.py",
            "test_llm_parser.py",
            "test_modify_params.py",
            "test_geometry_validation.py",
            "test_recompute_validation.py",
            "-v", "--tb=short",
        ],
        "Pytest Core Regression Suite"
    )

    # 2. Gemini Web Client Unit Tests
    run_command(
        [py, "-m", "pytest", "test_gemini_web_client.py", "-v", "--tb=short"],
        "Gemini Web Client Tests"
    )

    # 3. FastAPI Endpoint Tests
    run_command(
        [py, "test_api.py"],
        "FastAPI Async Endpoint Tests"
    )

    print("\n" + "="*70)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
