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
    GEMINI_WEB_BL,
    GEMINI_WEB_AUTH_USER,
    GEMINI_WEB_XSRF_TOKEN,
    GEMINI_WEB_PROXY,
    GEMINI_WEB_RETRY_ATTEMPTS,
    GEMINI_WEB_RETRY_DELAY_SEC,
    GEMINI_WEB_TIMEOUT_SEC,
)

logger = logging.getLogger("cad_workbench.gemini_web")

# ---------------------------------------------------------------------------
# Model Registry & Mapping
# ---------------------------------------------------------------------------

MODELS_CONFIG: Dict[str, Dict[str, Any]] = {
    "gemini-3.7-flash": {"mode": 1, "think": 4, "desc": "Gemini 3.7 Flash"},
    "gemini-3.6-flash": {"mode": 1, "think": 4, "desc": "Gemini 3.6 Flash"},
    "gemini-3.5-flash": {"mode": 1, "think": 4, "desc": "Gemini 3.5 Flash"},
    "gemini-3.5-flash-thinking": {"mode": 2, "think": 0, "desc": "Gemini Flash Thinking"},
    "gemini-3.5-flash-thinking-lite": {"mode": 5, "think": 0, "desc": "Gemini Flash Thinking Lite"},
    "gemini-3.1-pro": {"mode": 3, "think": 4, "desc": "Gemini Pro"},
    "gemini-3.1-pro-enhanced": {
        "mode": 3,
        "think": 4,
        "extra": {31: 2, 80: 3},
        "desc": "Gemini Pro Enhanced",
    },
    "gemini-2.5-flash": {"mode": 1, "think": 4, "desc": "Gemini 2.5 Flash"},
    "gemini-flash-latest": {"mode": 1, "think": 4, "desc": "Gemini Flash Latest"},
    "gemini-flash-lite": {"mode": 6, "think": 4, "desc": "Gemini Flash Lite"},
    "gemini-auto": {"mode": 4, "think": 4, "desc": "Gemini Auto"},
}

DEFAULT_MODEL = "gemini-3.6-flash"


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


def account_prefix() -> str:
    """Returns the Gemini account URL prefix for non-default Google accounts."""
    if not GEMINI_WEB_AUTH_USER:
        return ""
    return f"/u/{GEMINI_WEB_AUTH_USER}"


# ---------------------------------------------------------------------------
# Protocol & Payload Construction
# ---------------------------------------------------------------------------

def resolve_model_specs(model_name: str) -> Tuple[str, int, int, Optional[Dict[int, Any]]]:
    """Resolves model string to (model_name, mode_id, think_mode, extra_fields)."""
    norm = (model_name or DEFAULT_MODEL).strip().lower()
    think_override = None
    if "@think=" in norm:
        norm, think_str = norm.rsplit("@think=", 1)
        try:
            think_override = int(think_str)
        except ValueError:
            logger.warning(f"[Gemini Web] Invalid think override '{think_str}', using model default.")

    cfg = MODELS_CONFIG.get(norm)
    if not cfg:
        logger.warning(f"[Gemini Web] Unknown model '{norm}', falling back to '{DEFAULT_MODEL}'.")
        norm = DEFAULT_MODEL
        cfg = MODELS_CONFIG[DEFAULT_MODEL]

    think_mode = think_override if think_override is not None else cfg["think"]
    return norm, cfg["mode"], think_mode, cfg.get("extra")


def build_request_payload(
    prompt: str,
    model_id: int,
    think_mode: int,
    enforce_temporary_chat: bool = True,
    extra_fields: Optional[Dict[int, Any]] = None,
) -> str:
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
    if extra_fields:
        for index, value in extra_fields.items():
            inner[index] = value

    outer = [None, json.dumps(inner)]
    params = {"f.req": json.dumps(outer)}
    if GEMINI_WEB_XSRF_TOKEN:
        params["at"] = GEMINI_WEB_XSRF_TOKEN
    return urllib.parse.urlencode(params)


def build_request_headers(cookie_str: str, sapisid: Optional[str]) -> Dict[str, str]:
    """Builds required browser-mimicking headers with masked authorization."""
    prefix = account_prefix()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://gemini.google.com",
        "Referer": f"https://gemini.google.com{prefix}/app",
        "X-Same-Domain": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    }
    if GEMINI_WEB_AUTH_USER:
        headers["X-Goog-AuthUser"] = GEMINI_WEB_AUTH_USER
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
    timeout_sec: Optional[float] = None,
) -> str:
    """
    Executes an in-process generation request to Gemini Web with full error handling.
    Combines system_instruction with user prompt when provided.
    """
    if not GEMINI_WEB_ENABLED:
        raise GeminiWebError("Gemini Web client is disabled in configuration.")

    target_model = model or GEMINI_WEB_MODEL or DEFAULT_MODEL
    model_name, mode_id, think_mode, extra_fields = resolve_model_specs(target_model)

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
        extra_fields=extra_fields,
    )

    reqid = int(time.time()) % 1000000
    prefix = account_prefix()
    url = (
        f"https://gemini.google.com{prefix}/_/BardChatUi/data/"
        f"assistant.lamda.BardFrontendService/StreamGenerate"
        f"?bl={GEMINI_WEB_BL}&hl=en&_reqid={reqid}&rt=c"
    )

    headers = build_request_headers(cookie_str, sapisid)

    # Execute request over HTTPS with strict SSL verification
    last_error = None
    request_timeout = timeout_sec or GEMINI_WEB_TIMEOUT_SEC
    for attempt in range(max(GEMINI_WEB_RETRY_ATTEMPTS, 1)):
        try:
            transport = httpx.HTTPTransport(proxy=GEMINI_WEB_PROXY) if GEMINI_WEB_PROXY else None
            with httpx.Client(timeout=request_timeout, verify=True, transport=transport) as client:
                resp = client.post(url, content=payload_body.encode("utf-8"), headers=headers)
                resp.raise_for_status()
                raw_text = resp.text
            return parse_stream_response(raw_text)
        except httpx.TimeoutException as e:
            last_error = GeminiWebError(f"Gemini Web request timed out after {request_timeout}s: {e}")
        except httpx.HTTPStatusError as e:
            last_error = GeminiWebError(f"Gemini Web HTTP error {e.response.status_code}: {e.response.text[:200]}")
        except GeminiWebError as e:
            last_error = e
        except Exception as e:
            last_error = GeminiWebError(f"Gemini Web connection failure: {e}")

        if attempt < max(GEMINI_WEB_RETRY_ATTEMPTS, 1) - 1:
            time.sleep(GEMINI_WEB_RETRY_DELAY_SEC)

    raise last_error or GeminiWebError("Gemini Web generation failed.")
