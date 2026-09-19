/**
 * api.js — Comprehensive API Client for CAD Workbench
 *
 * Supports:
 * - JWT Auth token injection & refresh
 * - Authentication (Register, Login, Me)
 * - Project & Design Workspace Management
 * - Streaming Generation via SSE (Real-time pipeline phase updates)
 * - Backward-compatible generatePart, recomputePart, modifyPart
 */

import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || '';
const GENERATION_TIMEOUT = Number(import.meta.env.VITE_GENERATION_TIMEOUT_MS || 300_000);

export function resolveAssetUrl(path) {
  if (!path) return null;
  const baseUrl = BASE_URL.replace(/\/+$/, '');
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${baseUrl}${cleanPath}`;
}

// Token helper
export function getAuthToken() {
  return localStorage.getItem('cad_token');
}

export function setAuthToken(token) {
  if (token) {
    localStorage.setItem('cad_token', token);
  } else {
    localStorage.removeItem('cad_token');
  }
}

// Axios instance with auth interceptor
const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
});

api.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

const generationApi = axios.create({
  baseURL: BASE_URL,
  timeout: GENERATION_TIMEOUT,
});

generationApi.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

const recomputeApi = axios.create({
  baseURL: BASE_URL,
  timeout: 120_000,
});

recomputeApi.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ─── Authentication API ───────────────────────────────────────────────────

export async function registerUser({ email, password, display_name }) {
  const { data } = await api.post('/api/auth/register', {
    email,
    password,
    display_name,
  });
  const token = data.access_token || data.tokens?.access_token;
  if (token) {
    setAuthToken(token);
  }
  return data;
}

export async function loginUser({ email, password }) {
  const { data } = await api.post('/api/auth/login', {
    email,
    password,
  });
  const token = data.access_token || data.tokens?.access_token;
  if (token) {
    setAuthToken(token);
  }
  return data;
}

export async function fetchCurrentUser() {
  const token = getAuthToken();
  if (!token) return null;
  try {
    const { data } = await api.get('/api/auth/me');
    return data.user || data;
  } catch (err) {
    if (err.response?.status === 401) {
      setAuthToken(null);
    }
    return null;
  }
}

export function logoutUser() {
  setAuthToken(null);
}

// ─── Projects & Workspace API ─────────────────────────────────────────────

export async function listProjects() {
  const { data } = await api.get('/api/projects');
  return data.projects || [];
}

export async function createProject(name, description = '') {
  const { data } = await api.post('/api/projects', { name, description });
  return data.project;
}

export async function getProject(projectId) {
  const { data } = await api.get(`/api/projects/${projectId}`);
  return data;
}

export async function deleteProject(projectId) {
  const { data } = await api.delete(`/api/projects/${projectId}`);
  return data;
}

export async function getGenerationDetail(generationId) {
  const { data } = await api.get(`/api/generations/${generationId}`);
  return data.generation;
}

// ─── CAD Generation API ───────────────────────────────────────────────────

export async function healthCheck() {
  const { data } = await api.get('/api/health');
  return data;
}

export async function generatePart(prompt) {
  const { data } = await generationApi.post('/api/generate', { prompt });
  return data;
}

/**
 * Stream CAD generation with real-time SSE progress events.
 * @param {string} prompt - Part description
 * @param {(event: {phase: string, message: string, progress: number}) => void} onProgress
 * @returns {Promise<GenerateResponse>}
 */
export async function generatePartStream(prompt, onProgress) {
  const url = `${BASE_URL.replace(/\/+$/, '')}/api/generate/stream`;
  const token = getAuthToken();
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'text/event-stream',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify({ prompt }),
  });

  if (!response.ok) {
    const errJson = await response.json().catch(() => ({ detail: 'Network request failed' }));
    throw new Error(errJson.detail || errJson.error || `Server returned ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  let finalResult = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('data: ')) {
        const jsonStr = trimmed.slice(6);
        try {
          const parsed = JSON.parse(jsonStr);
          if (parsed.phase === 'complete') {
            finalResult = parsed.result;
          } else if (parsed.phase === 'error') {
            throw new Error(parsed.message || parsed.error || 'Generation failed');
          } else if (onProgress) {
            onProgress(parsed);
          }
        } catch (parseErr) {
          if (parseErr.message && !parseErr.message.includes('JSON')) {
            throw parseErr;
          }
        }
      }
    }
  }

  if (!finalResult) {
    throw new Error('Stream terminated before generation completed');
  }

  return finalResult;
}

export async function recomputePart(
  scriptId,
  pythonCode,
  updatedParameters,
  parameters = [],
  designMode = 'single_solid',
  components = null,
) {
  const { data } = await recomputeApi.post('/api/recompute', {
    script_id: scriptId,
    python_code: pythonCode,
    updated_parameters: updatedParameters,
    parameters,
    design_mode: designMode,
    components,
  });
  return data;
}

export async function modifyPart(
  scriptId,
  pythonCode,
  partName,
  modificationPrompt,
  parameters = [],
  designMode = 'single_solid',
  components = null,
) {
  const { data } = await generationApi.post('/api/modify', {
    script_id: scriptId,
    python_code: pythonCode,
    part_name: partName,
    modification_prompt: modificationPrompt,
    parameters,
    design_mode: designMode,
    components,
  });
  return data;
}

// ---------------------------------------------------------------------------
// Gallery API
// ---------------------------------------------------------------------------

export async function getGallery({ page = 1, perPage = 20, search = '', tag = '', sortBy = 'recent' } = {}) {
  const params = { page, per_page: perPage };
  if (search) params.search = search;
  if (tag) params.tag = tag;
  if (sortBy) params.sort_by = sortBy;
  const { data } = await api.get('/api/gallery', { params });
  return data;
}

export async function publishDesign(generationId, tags = []) {
  const { data } = await api.post(`/api/designs/${generationId}/publish`, tags);
  return data;
}

export async function unpublishDesign(generationId) {
  const { data } = await api.post(`/api/designs/${generationId}/unpublish`);
  return data;
}

export async function likeDesign(generationId) {
  const { data } = await api.post(`/api/designs/${generationId}/like`);
  return data;
}

export async function forkDesign(generationId, projectId = null) {
  const { data } = await api.post(`/api/designs/${generationId}/fork`, null, {
    params: projectId ? { project_id: projectId } : {},
  });
  return data;
}

export async function getMetrics() {
  const { data } = await api.get('/api/metrics');
  return data;
}

