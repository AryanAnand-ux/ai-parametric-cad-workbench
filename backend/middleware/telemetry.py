"""
Telemetry Middleware — Structured JSON Request Logging
======================================================
Captures every API request and emits a single structured JSON log line
with: timestamp, method, path, user_id, status_code, latency_ms, and
CAD-specific context (script_id when present in request body or path).

Usage: app.add_middleware(TelemetryMiddleware)
"""

import time
import json
import uuid
import logging
from typing import Optional
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("cad_workbench.telemetry")

# ---------------------------------------------------------------------------
# In-Memory Lightweight Metrics Store (no external dependency)
# ---------------------------------------------------------------------------
# Tracks counters and latency histograms in process memory.
# For production, replace with Prometheus or Datadog client.

class _MetricsStore:
    """Thread-safe-ish in-process metrics (good enough for single-process uvicorn)."""

    def __init__(self):
        self.request_count: int = 0
        self.error_count: int = 0
        # path → list of latency_ms (keep last 500 per path)
        self.latencies: dict[str, deque] = defaultdict(lambda: deque(maxlen=500))
        # status_code → count
        self.status_counts: dict[int, int] = defaultdict(int)
        # model used → generation count
        self.model_counts: dict[str, int] = defaultdict(int)
        # cad generation success / failure counts
        self.cad_success: int = 0
        self.cad_failure: int = 0

    def record(self, path: str, status: int, latency_ms: float):
        self.request_count += 1
        self.latencies[path].append(latency_ms)
        self.status_counts[status] += 1
        if status >= 400:
            self.error_count += 1

    def record_generation(self, success: bool, model: str = "unknown"):
        if success:
            self.cad_success += 1
        else:
            self.cad_failure += 1
        self.model_counts[model] += 1

    def summary(self) -> dict:
        total = self.request_count or 1
        all_latencies = [v for dq in self.latencies.values() for v in dq]
        avg_latency = sum(all_latencies) / len(all_latencies) if all_latencies else 0
        p95_latency = sorted(all_latencies)[int(len(all_latencies) * 0.95)] if all_latencies else 0

        return {
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate_pct": round(self.error_count / total * 100, 2),
            "cad_generations": {
                "success": self.cad_success,
                "failure": self.cad_failure,
                "success_rate_pct": round(
                    self.cad_success / max(self.cad_success + self.cad_failure, 1) * 100, 1
                ),
            },
            "status_codes": dict(self.status_counts),
            "models_used": dict(self.model_counts),
            "latency_ms": {
                "avg": round(avg_latency, 1),
                "p95": round(p95_latency, 1),
            },
            "per_path_avg_ms": {
                path: round(sum(dq) / len(dq), 1)
                for path, dq in self.latencies.items()
                if dq
            },
        }


# Singleton metrics store — imported by routes that need to record generation stats
metrics = _MetricsStore()


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class TelemetryMiddleware(BaseHTTPMiddleware):
    """
    Emits one structured JSON log line per request.

    Log format:
        {
            "ts": "<ISO timestamp>",
            "request_id": "<uuid>",
            "method": "POST",
            "path": "/api/generate",
            "status": 200,
            "latency_ms": 234,
            "user_id": "<jwt sub or null>",
        }
    """

    # Paths to skip (static file serving — too noisy)
    _SKIP_PREFIXES = ("/static/", "/docs", "/redoc", "/openapi.json")

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip static and docs routes
        path = request.url.path
        if any(path.startswith(p) for p in self._SKIP_PREFIXES):
            return await call_next(request)

        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()

        # Extract user_id from Authorization header if present (JWT sub claim)
        user_id: Optional[str] = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                import jose.jwt as _jwt
                import os
                token = auth_header[7:]
                # Decode without verification just to extract sub for logging
                payload = _jwt.get_unverified_claims(token)
                user_id = payload.get("sub")
            except Exception:
                pass

        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

        # Record metrics
        metrics.record(path, response.status_code, elapsed_ms)

        # Emit structured log line
        log_record = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "rid": request_id,
            "method": request.method,
            "path": path,
            "status": response.status_code,
            "ms": elapsed_ms,
            "user": user_id,
        }

        level = logging.WARNING if response.status_code >= 400 else logging.INFO
        logger.log(level, json.dumps(log_record))

        # Attach request-id to response headers for tracing
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{elapsed_ms}ms"
        return response
