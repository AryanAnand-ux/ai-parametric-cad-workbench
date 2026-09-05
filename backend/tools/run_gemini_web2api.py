"""
Standalone Gemini-Web2API Proxy Server
======================================
Runs a local, secure OpenAI-compatible HTTP server providing access to
Gemini Web endpoints (/v1/chat/completions and /v1/models).

Security Hardening:
  1. Strictly binds to loopback (127.0.0.1) by default to prevent external access.
  2. Enforces optional Bearer token authentication via GEMINI_WEB2API_KEY.
  3. Automatically sets temporary chat privacy flags on all outgoing requests.
  4. Sanitizes all console logs (zero credentials logged).

Usage:
  python tools/run_gemini_web2api.py [--port 8081] [--host 127.0.0.1]
"""

import sys
import os
import time
import json
import uuid
import logging
import argparse
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (
    GEMINI_WEB2API_HOST,
    GEMINI_WEB2API_PORT,
    GEMINI_WEB2API_KEY,
    GEMINI_WEB_MODEL,
)
from services import gemini_web_client

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("gemini_web2api_proxy")


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class SecureOpenAIProxyHandler(BaseHTTPRequestHandler):
    server_version = "GeminiWeb2API-Secure/1.0"

    def log_message(self, fmt, *args):
        client_ip = self.client_address[0] if self.client_address else "-"
        logger.info(f"{client_ip} - {fmt % args}")

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, message: str, status: int = 400, err_type: str = "invalid_request_error"):
        self._send_json({
            "error": {
                "message": message,
                "type": err_type,
                "param": None,
                "code": status
            }
        }, status=status)

    def _is_authorized(self) -> bool:
        """Enforce Bearer token check if GEMINI_WEB2API_KEY is configured."""
        required_key = GEMINI_WEB2API_KEY.strip()
        if not required_key:
            return True  # No auth required if key is empty
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            return token == required_key
        return False

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        if not self._is_authorized():
            return self._send_error("Unauthorized. Provide valid Bearer token.", status=401, err_type="authentication_error")

        if self.path in ("/v1/models", "/models"):
            models_list = [
                {"id": m, "object": "model", "created": int(time.time()), "owned_by": "google-gemini-web"}
                for m in gemini_web_client.MODELS_CONFIG.keys()
            ]
            return self._send_json({"object": "list", "data": models_list})

        if self.path in ("/", "/health"):
            cookie_str, _ = gemini_web_client.get_cookie_credentials()
            return self._send_json({
                "status": "online",
                "service": "Gemini-Web2API Secure Proxy",
                "authenticated": bool(cookie_str),
                "timestamp": time.time()
            })

        self._send_error("Endpoint not found", status=404)

    def do_POST(self):
        if not self._is_authorized():
            return self._send_error("Unauthorized. Provide valid Bearer token.", status=401, err_type="authentication_error")

        if self.path not in ("/v1/chat/completions", "/chat/completions"):
            return self._send_error("Endpoint not found", status=404)

        # Read body
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length == 0:
                return self._send_error("Empty request body")
            raw_body = self.rfile.read(length).decode("utf-8")
            data = json.loads(raw_body)
        except Exception as e:
            return self._send_error(f"Malformed JSON body: {e}")

        messages = data.get("messages", [])
        if not messages:
            return self._send_error("No 'messages' list provided")

        model = data.get("model", GEMINI_WEB_MODEL or "gemini-2.5-flash")

        # Extract system prompt and user prompts
        system_parts = []
        user_parts = []
        for msg in messages:
            role = msg.get("role", "user").lower()
            content = msg.get("content", "")
            if isinstance(content, list):
                # Simple text extraction for content blocks
                text_parts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
                content = "\n".join(text_parts)
            if role in ("system", "developer"):
                system_parts.append(str(content))
            else:
                user_parts.append(f"{role.upper()}: {content}")

        system_instruction = "\n\n".join(system_parts) if system_parts else None
        user_prompt = "\n\n".join(user_parts)

        # Execute web generation
        try:
            generated_text = gemini_web_client.generate(
                prompt=user_prompt,
                system_instruction=system_instruction,
                model=model,
                timeout_sec=90.0,
            )
        except gemini_web_client.GeminiWebError as e:
            logger.error(f"Gemini Web generation failed: {e}")
            return self._send_error(f"Gemini Web Upstream Error: {e}", status=502)
        except Exception as e:
            logger.error(f"Unexpected generation failure: {e}")
            return self._send_error(f"Internal server error: {e}", status=500)

        # Build standard OpenAI chat completion response
        completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        created_ts = int(time.time())
        token_estimate = len(generated_text) // 4

        response_payload = {
            "id": completion_id,
            "object": "chat.completion",
            "created": created_ts,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": generated_text,
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": len(user_prompt) // 4,
                "completion_tokens": token_estimate,
                "total_tokens": (len(user_prompt) // 4) + token_estimate
            }
        }

        self._send_json(response_payload)


def main():
    parser = argparse.ArgumentParser(description="Secure Gemini-Web2API Local Proxy")
    parser.add_argument("--host", default=GEMINI_WEB2API_HOST, help="Host binding (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=GEMINI_WEB2API_PORT, help="Port (default: 8081)")
    args = parser.parse_args()

    # Security assertion: Warn if host is not localhost
    if args.host not in ("127.0.0.1", "localhost", "::1"):
        logger.warning(
            f"[SECURITY WARNING] Binding to non-loopback interface '{args.host}'. "
            f"This exposes your Gemini Web proxy to the network!"
        )

    server_address = (args.host, args.port)
    httpd = ThreadedHTTPServer(server_address, SecureOpenAIProxyHandler)

    cookie_str, _ = gemini_web_client.get_cookie_credentials()
    auth_status = "Cookie Active" if cookie_str else "Anonymous Mode (No Cookie)"
    auth_req = "Bearer Token Enforced" if GEMINI_WEB2API_KEY else "Open Localhost"

    logger.info("==================================================================")
    logger.info("  Secure Gemini-Web2API OpenAI Proxy Server Started")
    logger.info(f"  URL:            http://{args.host}:{args.port}/v1")
    logger.info(f"  Gemini Web:     {auth_status}")
    logger.info(f"  Access Auth:    {auth_req}")
    logger.info("  Privacy:        temporary_chats=True (zero history retention)")
    logger.info("==================================================================")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down proxy server...")
        httpd.shutdown()


if __name__ == "__main__":
    main()
