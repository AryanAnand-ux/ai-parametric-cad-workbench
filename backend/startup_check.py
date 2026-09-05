"""
startup_check.py — Quick sanity check before running the server.
Run this once to verify all dependencies are correctly installed.
"""
import sys
import importlib

REQUIRED = [
    ("fastapi",              "FastAPI web framework"),
    ("uvicorn",              "ASGI server"),
    ("pydantic",             "Data validation (v2)"),
    ("google.genai",         "Gemini API client"),
    ("groq",                 "Groq API client"),
    ("build123d",            "CAD geometry engine (OCCT)"),
    ("chromadb",             "Vector store for RAG"),
    ("sentence_transformers","Local embedding model"),
    ("trimesh",              "STL mesh inspection"),
    ("dotenv",               "Environment variable loading"),
]

print("=" * 60)
print(" AI CAD Workbench — Startup Dependency Check")
print("=" * 60)

ok = True
for module, label in REQUIRED:
    try:
        importlib.import_module(module)
        print(f"  [OK]   {label:<36} ({module})")
    except ImportError as e:
        print(f"  [FAIL] {label:<36} ({module}) — {e}")
        ok = False

print("=" * 60)

# Check API keys
import os
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).resolve().parent / ".env")
load_dotenv()

gemini_key = os.getenv("GEMINI_API_KEY", "")
groq_key   = os.getenv("GROQ_API_KEY", "")
web_cookie = os.getenv("GEMINI_WEB_COOKIE", "")
web_enabled = os.getenv("GEMINI_WEB_ENABLED", "false").lower() in ("true", "1", "yes")

print(f"  [{'OK' if gemini_key else 'WARN'}]   GEMINI_API_KEY {'configured' if gemini_key else 'NOT SET (Gemini API tiers will fail)'}")
print(f"  [{'OK' if web_enabled else 'WARN'}]   GEMINI_WEB     {'enabled (' + ('cookie-authenticated' if web_cookie else 'anonymous zero-auth') + ')' if web_enabled else 'disabled'}")
print(f"  [{'OK' if groq_key else 'WARN'}]   GROQ_API_KEY   {'configured' if groq_key else 'NOT SET (Groq fallback unavailable)'}")

print("=" * 60)

# Check RAG index
try:
    from services.rag_service import RAGService
    count = RAGService.index_size()
    print(f"  [{'OK' if count > 0 else 'WARN'}]   ChromaDB RAG index: {count} examples indexed")
    if count == 0:
        print("         Run `python -c \"from services.rag_service import RAGService; RAGService.build_index()\"` to index.")
except Exception as e:
    print(f"  [FAIL] ChromaDB RAG index check failed: {e}")
    ok = False

print("=" * 60)
if ok:
    print("  All checks passed. Start server with: uvicorn main:app --reload")
else:
    print("  Some checks failed — install missing packages with: pip install -r requirements.txt")
print("=" * 60)

sys.exit(0 if ok else 1)
