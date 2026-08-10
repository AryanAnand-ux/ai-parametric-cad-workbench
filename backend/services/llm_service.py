"""
LLM Service — 3-Tier Dual-Model Strategy with RAG Context Injection
====================================================================
Tier 1 (Primary)   : Gemini 2.0 Flash  (google-genai, native JSON mode, free tier)
Tier 2 (Secondary) : Gemini 2.5 Flash  (google-genai, separate quota pool)
Tier 3 (Fallback)  : Groq Llama-3.3-70B (10x faster inference, always-on free tier)

Flow:
  1. Retrieve top-3 similar build123d CAD examples from ChromaDB via RAG.
  2. Dynamically construct system prompt with few-shot example block.
  3. Try Gemini 2.0 Flash first.
  4. Fallback to Gemini 2.5 Flash if quota/rate limited.
  5. Fallback to Groq Llama-3.3-70B if both Gemini fail.
  6. Self-correction loop (up to 3 retries) on execution error.
"""

import os
import json
import logging
from typing import Tuple, Optional

from pydantic import ValidationError

from config import GEMINI_API_KEY, GROQ_API_KEY
from schemas import DualOutputPayload
from services.prompts import BUILD123D_SYSTEM_PROMPT, CORRECTION_PROMPT_TEMPLATE
from services.rag_service import RAGService

logger = logging.getLogger("cad_workbench.llm_service")


# ---------------------------------------------------------------------------
# Response Parser (shared by all model tiers)
# ---------------------------------------------------------------------------

def _parse_response(raw_text: str) -> DualOutputPayload:
    """
    Parses raw LLM text into a validated DualOutputPayload.
    Handles accidental markdown fences gracefully.
    """
    text = raw_text.strip()

    # Strip markdown fences if present despite JSON mode
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        ).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {e}\nRaw snippet: {raw_text[:300]}")

    try:
        return DualOutputPayload(**data)
    except (ValidationError, TypeError) as e:
        raise ValueError(f"Response failed schema validation: {e}")


# ---------------------------------------------------------------------------
# Gemini Client (Tier 1: gemini-2.0-flash, Tier 2: gemini-2.5-flash)
# ---------------------------------------------------------------------------

def _call_gemini(prompt: str, system: str, model: str = "gemini-2.0-flash") -> str:
    """Calls a Gemini model with native JSON mode enforcement."""
    from google import genai
    from google.genai import types

    api_key = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not configured.")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            temperature=0.2,
            max_output_tokens=8192,
        )
    )
    return response.text


# ---------------------------------------------------------------------------
# Groq Client (Tier 3: llama-3.3-70b-versatile)
# ---------------------------------------------------------------------------

def _call_groq(prompt: str, system: str) -> str:
    """
    Calls Groq Llama-3.3-70B as a high-speed tertiary fallback.
    Uses JSON mode enforcement via response_format.
    """
    from groq import Groq

    api_key = GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not configured.")

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=8192,
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Main LLM Service Class
# ---------------------------------------------------------------------------

class LLMService:
    """
    3-Tier LLM orchestrator with build123d context and RAG dynamic few-shot injection.
    """

    MAX_RETRIES = 3

    @classmethod
    def _construct_system_prompt(cls, user_prompt: str) -> str:
        """
        Retrieves top-3 RAG examples for user_prompt and injects into BUILD123D_SYSTEM_PROMPT.
        """
        try:
            rag_examples = RAGService.retrieve(user_prompt, k=3)
            examples_block = RAGService.format_for_prompt(rag_examples)
        except Exception as e:
            logger.warning(f"[RAG] Failed to retrieve RAG examples: {e}")
            examples_block = ""

        return BUILD123D_SYSTEM_PROMPT.format(rag_examples_block=examples_block)

    @classmethod
    def _call_with_fallback(cls, prompt: str, system: str) -> Tuple[str, str]:
        """
        3-tier fallback chain. Returns (raw_json_string, model_name_used).
        """
        errors = []

        # --- Tier 1: Gemini 2.0 Flash ---
        try:
            logger.info("[LLM] Calling Gemini 2.0 Flash (Tier 1)...")
            raw = _call_gemini(prompt, system, model="gemini-2.0-flash")
            logger.info(f"[LLM] Gemini 2.0 Flash responded ({len(raw)} chars)")
            return raw, "gemini-2.0-flash"
        except Exception as e:
            errors.append(f"gemini-2.0-flash: {e}")
            logger.warning(f"[LLM] Tier 1 failed: {e}")

        # --- Tier 2: Gemini 2.5 Flash ---
        try:
            logger.info("[LLM] Calling Gemini 2.5 Flash (Tier 2)...")
            raw = _call_gemini(prompt, system, model="gemini-2.5-flash")
            logger.info(f"[LLM] Gemini 2.5 Flash responded ({len(raw)} chars)")
            return raw, "gemini-2.5-flash"
        except Exception as e:
            errors.append(f"gemini-2.5-flash: {e}")
            logger.warning(f"[LLM] Tier 2 failed: {e}")

        # --- Tier 3: Groq Llama-3.3-70B ---
        try:
            logger.info("[LLM] Calling Groq Llama-3.3-70B (Tier 3)...")
            raw = _call_groq(prompt, system)
            logger.info(f"[LLM] Groq Llama-3.3-70B responded ({len(raw)} chars)")
            return raw, "groq-llama-3.3-70b"
        except Exception as e:
            errors.append(f"groq-llama-3.3-70b: {e}")
            logger.error("[LLM] All 3 tiers failed.")

        raise RuntimeError("All 3 LLM providers failed.\n" + "\n".join(errors))

    @classmethod
    def generate_dual_output(cls, user_prompt: str) -> Tuple[DualOutputPayload, str]:
        """
        Generates a DualOutputPayload (python_code + parameters) for build123d.
        Uses RAG to dynamically retrieve few-shot examples for the system prompt.
        Returns (DualOutputPayload, model_name_used).
        """
        system = cls._construct_system_prompt(user_prompt)
        raw, model_used = cls._call_with_fallback(user_prompt, system=system)
        payload = _parse_response(raw)
        logger.info(
            f"[LLM] Generated '{payload.part_name}' | "
            f"{len(payload.parameters)} params | model={model_used}"
        )
        return payload, model_used

    @classmethod
    def correct_code(
        cls,
        user_prompt: str,
        failed_code: str,
        error_traceback: str
    ) -> Tuple[DualOutputPayload, str]:
        """
        Sends broken build123d script + traceback back to LLM for self-correction.
        """
        truncated_traceback = error_traceback[-1500:] if len(error_traceback) > 1500 else error_traceback

        correction_prompt = CORRECTION_PROMPT_TEMPLATE.format(
            user_prompt=user_prompt,
            failed_code=failed_code,
            error_traceback=truncated_traceback
        )
        system = cls._construct_system_prompt(user_prompt)
        logger.info("[LLM] Sending build123d self-correction prompt...")
        raw, model_used = cls._call_with_fallback(correction_prompt, system=system)
        payload = _parse_response(raw)
        logger.info(f"[LLM] Correction successful | model={model_used}")
        return payload, model_used

    # Expose parser for tests
    @staticmethod
    def _parse_response(raw_json: str) -> DualOutputPayload:
        return _parse_response(raw_json)
