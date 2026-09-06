"""
clean_artifacts.py — Cross-platform artifact cleanup script.

Cleans:
  - Python bytecode and __pycache__ directories
  - Stale temporary CAD model files under scratch/ (STL/STEP/PY artifacts)
  - Frontend build cache/artifacts (dist)
"""

import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def clean():
    print(f"Cleaning repository artifacts at: {REPO_ROOT}")
    removed_files = 0
    removed_dirs = 0

    # 1. Clean __pycache__ and *.pyc
    for root, dirs, files in os.walk(REPO_ROOT):
        # Skip .git and venv
        if ".git" in dirs:
            dirs.remove(".git")
        if "venv" in dirs:
            dirs.remove("venv")
        if "node_modules" in dirs:
            dirs.remove("node_modules")

        for d in list(dirs):
            if d == "__pycache__":
                cache_path = Path(root) / d
                shutil.rmtree(cache_path, ignore_errors=True)
                removed_dirs += 1
                dirs.remove(d)

        for f in files:
            if f.endswith((".pyc", ".pyo", ".pyd")):
                try:
                    (Path(root) / f).unlink()
                    removed_files += 1
                except OSError:
                    pass

    # 2. Clean scratch/temp artifacts (STL/STEP/PY outputs live under scratch/temp)
    scratch_dir = REPO_ROOT / "scratch"
    if scratch_dir.exists():
        for item in scratch_dir.glob("**/*"):
            if item.is_file():
                try:
                    item.unlink()
                    removed_files += 1
                except OSError:
                    pass

    # 4. Clean frontend/dist
    frontend_dist = REPO_ROOT / "frontend" / "dist"
    if frontend_dist.exists():
        shutil.rmtree(frontend_dist, ignore_errors=True)
        removed_dirs += 1

    print(f"[OK] Clean complete. Removed {removed_files} files and {removed_dirs} directories.")


if __name__ == "__main__":
    clean()
