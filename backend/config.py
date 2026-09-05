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

# Gemini Web (Reverse-Engineered Web2API Integration)
# Allows zero-auth or cookie-authenticated generation directly via Gemini Web
GEMINI_WEB_ENABLED = os.getenv("GEMINI_WEB_ENABLED", "false").strip().lower() in ("true", "1", "yes")
GEMINI_WEB_COOKIE = os.getenv("GEMINI_WEB_COOKIE", "")
GEMINI_WEB_COOKIE_FILE = os.getenv("GEMINI_WEB_COOKIE_FILE", str(BASE_DIR / ".gemini_cookie"))
GEMINI_WEB_MODEL = os.getenv("GEMINI_WEB_MODEL", "gemini-3.6-flash")
GEMINI_WEB_BL = os.getenv("GEMINI_WEB_BL", "boq_assistant-bard-web-server_20260716.08_p0")
GEMINI_WEB_AUTH_USER = os.getenv("GEMINI_WEB_AUTH_USER", "").strip()
GEMINI_WEB_XSRF_TOKEN = os.getenv("GEMINI_WEB_XSRF_TOKEN", "").strip()
GEMINI_WEB_PROXY = os.getenv("GEMINI_WEB_PROXY", "").strip()
GEMINI_WEB_RETRY_ATTEMPTS = int(os.getenv("GEMINI_WEB_RETRY_ATTEMPTS", "3"))
GEMINI_WEB_RETRY_DELAY_SEC = float(os.getenv("GEMINI_WEB_RETRY_DELAY_SEC", "2"))
GEMINI_WEB_TIMEOUT_SEC = float(os.getenv("GEMINI_WEB_TIMEOUT_SEC", "180"))

# Standalone Gemini-Web2API Proxy Service Settings
GEMINI_WEB2API_HOST = os.getenv("GEMINI_WEB2API_HOST", "127.0.0.1")  # Strictly loopback for security
GEMINI_WEB2API_PORT = int(os.getenv("GEMINI_WEB2API_PORT", "8081"))
GEMINI_WEB2API_KEY = os.getenv("GEMINI_WEB2API_KEY", "")  # Optional Bearer token for localhost auth

# API boundary settings
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "").strip()
ALLOWED_ORIGINS = [
	origin.strip()
	for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
	if origin.strip()
]
RELOAD = os.getenv("RELOAD", "false").strip().lower() in ("true", "1", "yes")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip().lower()
CAD_MAX_CONCURRENT_EXECUTIONS = int(os.getenv("CAD_MAX_CONCURRENT_EXECUTIONS", "2"))
CAD_EXECUTION_TIMEOUT_SECONDS = int(os.getenv("CAD_EXECUTION_TIMEOUT_SECONDS", "60"))
RAG_BUILD_ON_STARTUP = os.getenv("RAG_BUILD_ON_STARTUP", "false").strip().lower() in ("true", "1", "yes")
