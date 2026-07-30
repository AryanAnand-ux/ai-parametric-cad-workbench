import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
MODELS_DIR = TEMP_DIR / "models"

# Ensure temporary directories exist
TEMP_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# FreeCAD / CadQuery Configuration
FREECAD_CMD = os.getenv("FREECAD_CMD", "FreeCADCmd")
PYTHON_EXEC = os.getenv("PYTHON_EXEC", str(BASE_DIR / "venv" / "Scripts" / "python.exe"))

# API & Server Configuration
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
