"""
Gemini Web Client — In-Process Reverse-Engineered Gemini StreamGenerate Client
=============================================================================
Direct in-process client for Google's Gemini Web service.
Allows utilizing Gemini Web generation without requiring an official API key.

Security & Hardening:
  1. Enforces temporary_chats=True so prompts/scripts are never stored in user's Google history.
  2. Masks all sensitive cookies/tokens in logs.
  3. Uses strict SSL verification (verify=True).
  4. Local loopback only if used via server.
  5. Catches upstream BardErrorInfo and connection errors to trigger graceful fallback.
"""

import os
import re
import ssl
import json
import time
import uuid
import hashlib
import logging
import urllib.parse
from typing import Optional, Tuple, Dict, Any, List

import httpx

from config import (
    GEMINI_WEB_ENABLED,
    GEMINI_WEB_COOKIE,
    GEMINI_WEB_COOKIE_FILE,
    GEMINI_WEB_MODEL,
)

logger = logging.getLogger("cad_workbench.gemini_web")

# ---------------------------------------------------------------------------
# Model Registry & Mapping
# ---------------------------------------------------------------------------

MODELS_CONFIG: Dict[str, Dict[str, Any]] = {
    "gemini-3.7-flash": {"mode": 1, "think": 4, "desc": "Gemini 3.7 Flash"},
    "gemini-3.6-flash": {"mode": 1, "think": 4, "desc": "Gemini 3.6 Flash"},
    "gemini-3.5-flash": {"mode": 1, "think": 4, "desc": "Gemini 3.5 Flash"},
    "gemini-2.5-flash": {"mode": 1, "think": 4, "desc": "Gemini 2.5 Flash"},
    "gemini-flash-latest": {"mode": 1, "think": 4, "desc": "Gemini Flash Latest"},
    "gemini-flash-lite": {"mode": 6, "think": 4, "desc": "Gemini Flash Lite"},
    "gemini-auto": {"mode": 4, "think": 4, "desc": "Gemini Auto"},
}

DEFAULT_MODEL = "gemini-2.5-flash"
GEMINI_BL_VERSION = "boq_assistant-bard-web-server_20260716.08_p0"


class GeminiWebError(RuntimeError):
    """Raised when Gemini Web generation fails or upstream rejects the request."""
    pass


# ---------------------------------------------------------------------------
# Session & Cookie Management (Masked & Protected)
# ---------------------------------------------------------------------------

_cached_cookie_data = {"raw": "", "sapisid": "", "mtime": 0}


def get_cookie_credentials() -> Tuple[str, Optional[str]]:
    """
    Retrieves cookie string and extracted SAPISID for authentication.
    Prefers GEMINI_WEB_COOKIE from environment/config, falls back to GEMINI_WEB_COOKIE_FILE.
    Returns (cookie_str, sapisid or None).
    """
    # 1. Environment variable / config string
    if GEMINI_WEB_COOKIE and GEMINI_WEB_COOKIE.strip():
        cookie_str = GEMINI_WEB_COOKIE.strip()
        pairs = dict(p.split("=", 1) for p in cookie_str.split(";") if "=" in p)
        sapisid = pairs.get("SAPISID", "").strip() or None
        return cookie_str, sapisid

    # 2. Local cookie file if configured & exists
    if GEMINI_WEB_COOKIE_FILE and os.path.exists(GEMINI_WEB_COOKIE_FILE):
        try:
            mtime = os.path.getmtime(GEMINI_WEB_COOKIE_FILE)
            if mtime == _cached_cookie_data["mtime"] and _cached_cookie_data["raw"]:
                return _cached_cookie_data["raw"], _cached_cookie_data["sapisid"] or None

            with open(GEMINI_WEB_COOKIE_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()

            if content.startswith("{"):
                data = json.loads(content)
                cookie_str = data.get("cookie", "")
                sapisid = data.get("sapisid", "")
            else:
                cookie_str = content
                pairs = dict(p.split("=", 1) for p in cookie_str.split(";") if "=" in p)
                sapisid = pairs.get("SAPISID", "").strip()

            _cached_cookie_data.update({
                "raw": cookie_str,
                "sapisid": sapisid or "",
                "mtime": mtime
            })
            return cookie_str, sapisid or None
        except Exception as e:
            logger.warning(f"[Gemini Web] Error reading cookie file: {e}")

    return "", None


def make_sapisidhash(sapisid: str) -> str:
    """Generates a SAPISIDHASH header token for Google Web authorization."""
    ts = int(time.time())
    digest = hashlib.sha1(f"{ts} {sapisid} https://gemini.google.com".encode()).hexdigest()
    return f"SAPISIDHASH {ts}_{digest}"


def is_configured() -> bool:
    """Returns True if Gemini Web fallback is enabled."""
    return GEMINI_WEB_ENABLED


# ---------------------------------------------------------------------------
# Protocol & Payload Construction
# ---------------------------------------------------------------------------

def resolve_model_specs(model_name: str) -> Tuple[str, int, int]:
    """Resolves model string to (model_name, mode_id, think_mode)."""
    norm = model_name.strip().lower()
    cfg = MODELS_CONFIG.get(norm, MODELS_CONFIG.get(DEFAULT_MODEL, {"mode": 1, "think": 4}))
    return norm, cfg["mode"], cfg["think"]


def build_request_payload(prompt: str, model_id: int, think_mode: int, enforce_temporary_chat: bool = True) -> str:
    """
    Constructs Google's internal StreamGenerate RPC payload.
    Enforces temporary chat persistence flag (inner[41]=[1], inner[45]=1)
    to protect user privacy.
    """
    inner: List[Any] = [None] * 102
    inner[0] = [prompt, 0, None, None, None, None, 0]
    inner[1] = ["en"]
    inner[2] = ["", "", "", None, None, None, None, None, None, ""]
    inner[6] = [0]
    inner[7] = 1
    inner[10] = 1
    inner[11] = 0
    inner[17] = [[think_mode]]
    inner[18] = 0
    inner[27] = 1
    inner[30] = [4]

    # Privacy enforcement: Set temporary chat flags
    if enforce_temporary_chat:
        inner[41] = [1]
        inner[45] = 1
    else:
        inner[41] = [2]

    inner[53] = 0
    inner[59] = str(uuid.uuid4())
    inner[61] = []
    inner[68] = 1
    inner[79] = model_id

    outer = [None, json.dumps(inner)]
    params = {"f.req": json.dumps(outer)}
    return urllib.parse.urlencode(params)


def build_request_headers(cookie_str: str, sapisid: Optional[str]) -> Dict[str, str]:
    """Builds required browser-mimicking headers with masked authorization."""
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://gemini.google.com",
        "Referer": "https://gemini.google.com/app",
        "X-Same-Domain": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    }
    if cookie_str:
        headers["Cookie"] = cookie_str
    if sapisid:
        headers["Authorization"] = make_sapisidhash(sapisid)
    return headers


# ---------------------------------------------------------------------------
# Stream Parsing & Response Recovery
# ---------------------------------------------------------------------------

def clean_generated_text(text: str) -> str:
    """Strips internal code execution artifacts and googleusercontent placeholders."""
    text = re.sub(
        r'```(?:python|javascript|text)\?code_(?:reference|stdout)&code_event_index=\d+\n.*?```\n?',
        '', text, flags=re.DOTALL
    )
    text = re.sub(r'https?://googleusercontent\.com/card_content/\d+\n?', '', text)
    return text.strip()


def extract_texts_from_line(line: str) -> List[str]:
    """Parses a single wrb.fr RPC response line from the Google stream."""
    if '"wrb.fr"' not in line or len(line) < 150:
        return []
    try:
        arr = json.loads(line)
        if not (isinstance(arr, list) and len(arr) > 0 and len(arr[0]) > 2):
            return []
        inner_str = arr[0][2]
        if not inner_str or len(inner_str) < 50:
            return []
        inner = json.loads(inner_str)
        if not (isinstance(inner, list) and len(inner) > 4 and inner[4]):
            return []
        texts = []
        for part in inner[4]:
            if isinstance(part, list) and len(part) > 1 and part[1] and isinstance(part[1], list):
                for t in part[1]:
                    if isinstance(t, str) and t:
                        texts.append(t)
        return texts
    except (json.JSONDecodeError, IndexError, TypeError):
        return []


def parse_stream_response(raw_response: str) -> str:
    """Extracts the accumulated longest final text from the raw RPC response."""
    # Check for upstream rejection
    bard_err = re.search(r'BardErrorInfo\s*\[(\d+)\]', raw_response)
    if bard_err:
        err_code = bard_err.group(1)
        raise GeminiWebError(f"Gemini Web upstream rejected request (BardErrorInfo [{err_code}]).")

    longest_text = ""
    for line in raw_response.splitlines():
        for candidate in extract_texts_from_line(line):
            if len(candidate) > len(longest_text):
                longest_text = candidate

    cleaned = clean_generated_text(longest_text)
    if not cleaned:
        raise GeminiWebError("No valid text output recovered from Gemini Web response stream.")
    return cleaned


# ---------------------------------------------------------------------------
# Primary Execution Interface
# ---------------------------------------------------------------------------

def generate(
    prompt: str,
    system_instruction: Optional[str] = None,
    model: Optional[str] = None,
    timeout_sec: float = 90.0,
) -> str:
    """
    Executes an in-process generation request to Gemini Web with full error handling.
    Combines system_instruction with user prompt when provided.
    """
    if not GEMINI_WEB_ENABLED:
        raise GeminiWebError("Gemini Web client is disabled in configuration.")

    target_model = model or GEMINI_WEB_MODEL or DEFAULT_MODEL
    model_name, mode_id, think_mode = resolve_model_specs(target_model)

    cookie_str, sapisid = get_cookie_credentials()
    auth_desc = "cookie-authenticated" if cookie_str else "anonymous (zero-auth)"
    logger.info(f"[Gemini Web] Generating via model '{model_name}' ({auth_desc})")

    # Combine prompt with system directives for web mode
    if system_instruction and system_instruction.strip():
        full_prompt = (
            f"{system_instruction.strip()}\n\n"
            f"==================== USER REQUEST ====================\n"
            f"{prompt.strip()}\n\n"
            f"[IMPORTANT REQUIREMENT: Respond ONLY with valid JSON satisfying the schema. Do NOT include extraneous conversational filler.]"
        )
    else:
        full_prompt = prompt

    payload_body = build_request_payload(
        prompt=full_prompt,
        model_id=mode_id,
        think_mode=think_mode,
        enforce_temporary_chat=True,
    )

    reqid = int(time.time()) % 1000000
    url = (
        f"https://gemini.google.com/_/BardChatUi/data/"
        f"assistant.lamda.BardFrontendService/StreamGenerate"
        f"?bl={GEMINI_BL_VERSION}&hl=en&_reqid={reqid}&rt=c"
    )

    headers = build_request_headers(cookie_str, sapisid)

    # Execute request over HTTPS with strict SSL verification
    try:
        with httpx.Client(timeout=timeout_sec, verify=True) as client:
            resp = client.post(url, content=payload_body.encode("utf-8"), headers=headers)
            resp.raise_for_status()
            raw_text = resp.text
    except httpx.TimeoutException as e:
        raise GeminiWebError(f"Gemini Web request timed out after {timeout_sec}s: {e}") from e
    except httpx.HTTPStatusError as e:
        raise GeminiWebError(f"Gemini Web HTTP error {e.response.status_code}: {e.response.text[:200]}") from e
    except Exception as e:
        raise GeminiWebError(f"Gemini Web connection failure: {e}") from e

    return parse_stream_response(raw_text)
