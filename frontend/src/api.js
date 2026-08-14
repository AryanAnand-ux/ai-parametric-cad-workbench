/**
 * api.js — API client for the CAD Workbench backend
 * Base URL auto-detects: dev server on :8000, same-origin in production
 */

import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 90_000,  // 90s — LLM generation can be slow on first run
});

/**
 * Generate a new parametric CAD part from a natural language prompt.
 * @param {string} prompt
 * @returns {Promise<GenerateResponse>}
 */
export async function generatePart(prompt) {
  const { data } = await api.post('/api/generate', { prompt });
  return data;
}

/**
 * Recompute a part with updated slider values (no LLM call — very fast).
 * @param {string} scriptId
 * @param {string} pythonCode
 * @param {Record<string, number>} updatedParameters
 * @returns {Promise<RecomputeResponse>}
 */
export async function recomputePart(scriptId, pythonCode, updatedParameters) {
  const { data } = await api.post('/api/recompute', {
    script_id: scriptId,
    python_code: pythonCode,
    updated_parameters: updatedParameters,
  });
  return data;
}

/**
 * Health check — verifies backend is online.
 * @returns {Promise<HealthResponse>}
 */
export async function healthCheck() {
  const { data } = await api.get('/api/health');
  return data;
}

export const STL_URL = (path) => `${BASE_URL}${path}`;
export const STEP_URL = (path) => `${BASE_URL}${path}`;
