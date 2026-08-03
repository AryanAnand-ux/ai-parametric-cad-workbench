import os
import sys
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
MODELS_DIR = TEMP_DIR / "models"

# Ensure temporary directories exist
TEMP_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# FreeCAD / CadQuery Configuration
# PYTHON_EXEC: cross-platform venv python path
_venv_python = BASE_DIR / "venv" / ("Scripts" if sys.platform == "win32" else "bin") / "python"
FREECAD_CMD = os.getenv("FREECAD_CMD", "FreeCADCmd")
PYTHON_EXEC = os.getenv("PYTHON_EXEC", str(_venv_python))

# API & Server Configuration
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")

# LLM API Keys (centralized)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
