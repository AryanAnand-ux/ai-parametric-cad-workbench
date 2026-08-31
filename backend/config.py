import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure .env is loaded before reading any environment variables
load_dotenv(Path(__file__).resolve().parent / ".env")
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent

# ── Temp directory: placed OUTSIDE the backend source tree so that
# uvicorn's WatchFiles reloader never sees generated .py/.stl/.step files
# and does NOT restart the server mid-request (which caused 500 errors).
TEMP_DIR    = BASE_DIR.parent / "scratch" / "temp"
MODELS_DIR  = TEMP_DIR / "models"

# Ensure temporary directories exist
TEMP_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Python executable: prefer the venv interpreter when present,
# fall back to sys.executable so Docker / CI environments work without a venv.
_venv_python = BASE_DIR / "venv" / ("Scripts" if sys.platform == "win32" else "bin") / "python"
_default_python = str(_venv_python) if _venv_python.exists() else sys.executable
PYTHON_EXEC = os.getenv("PYTHON_EXEC", _default_python)

# API & Server Configuration
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")

# LLM API Keys (centralized)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
