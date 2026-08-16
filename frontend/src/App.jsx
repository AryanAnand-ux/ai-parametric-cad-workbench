/**
 * App.jsx — AI-Driven Parametric CAD Workbench App Shell
 * Features:
 *   - Natural language prompt submission to /api/generate
 *   - Sub-200ms debounced parametric recomputation via /api/recompute
 *   - React Three Fiber 3D WebGL preview (STL)
 *   - STEP & STL download buttons
 *   - Model info, metrics, and error state handling
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import Viewer3D from './components/Viewer3D';
import ParameterSlider from './components/ParameterSlider';
import { generatePart, recomputePart, healthCheck, modifyPart } from './api';

// Build a full URL for file downloads (works via Vite proxy in dev)
const fileUrl = (path) => path ? `${import.meta.env.VITE_API_URL || ''}${path}` : null;

const PRESET_PROMPTS = [
  "A mounting bracket with four corner M5 holes",
  "A hollow cylinder with 20mm radius and 3mm wall thickness",
  "A rectangular box 60mm x 40mm x 25mm with chamfered top edges",
  "An L-bracket with two perpendicular 60mm arms",
  "A flanged bushing with 10mm inner bore and 20mm outer flange"
];

export default function App() {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [recomputing, setRecomputing] = useState(false);
  const [error, setError] = useState(null);

  // Response state from /api/generate
  const [scriptId, setScriptId] = useState(null);
  const [partName, setPartName] = useState(null);
  const [description, setDescription] = useState(null);
  const [pythonCode, setPythonCode] = useState(null);
  const [parameters, setParameters] = useState([]);
  const [paramValues, setParamValues] = useState({});
  const [meshUrl, setMeshUrl] = useState(null);
  const [stepUrl, setStepUrl] = useState(null);
  const [meshInfo, setMeshInfo] = useState(null);
  const [recompTime, setRecompTime] = useState(null);
  const [modelUsed, setModelUsed] = useState(null);
  const [backendStatus, setBackendStatus] = useState('checking');

  // UI Toggle States
  const [wireframe, setWireframe] = useState(false);
  const [showCodeModal, setShowCodeModal] = useState(false);
  const viewerRef = useRef(null);

  // Chat-to-Modify state
  const [chatHistory, setChatHistory] = useState([]);
  const [modifyPrompt, setModifyPrompt] = useState('');
  const [modifying, setModifying] = useState(false);
  const chatEndRef = useRef(null);

  // Debounce timer for slider recomputation
  const debounceTimerRef = useRef(null);

  // Health check on mount + debounce timer cleanup on unmount
  useEffect(() => {
    healthCheck()
      .then((data) => setBackendStatus(data.status === 'online' ? 'online' : 'offline'))
      .catch(() => setBackendStatus('offline'));

    return () => {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    };
  }, []);

  // Apply full response from generate OR modify to shared state
  const applyPartResponse = (res) => {
    setScriptId(res.script_id);
    setPartName(res.part_name);
    setDescription(res.description);
    setPythonCode(res.python_code);
    setParameters(res.parameters || []);
    setMeshUrl(res.mesh_url);
    setStepUrl(res.step_url);
    setMeshInfo(res.mesh_info || {});
    setRecompTime(res.recomputation_time_ms);
    setModelUsed(res.model_used);
    const initialValues = {};
    (res.parameters || []).forEach((p) => { initialValues[p.name] = p.default; });
    setParamValues(initialValues);
  };

  // Submit prompt -> /api/generate
  const handleGenerate = async (overridePrompt) => {
    const activePrompt = overridePrompt || prompt;
    if (!activePrompt.trim() || loading) return;

    setLoading(true);
    setError(null);
    setChatHistory([]); // Reset chat on new generation

    try {
      const res = await generatePart(activePrompt);
      applyPartResponse(res);
    } catch (err) {
      console.error('[Generate error]', err);
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : err.message || 'Generation failed.');
    } finally {
      setLoading(false);
    }
  };

  // Chat-to-Modify -> /api/modify
  const handleModify = async () => {
    if (!modifyPrompt.trim() || modifying || !scriptId || !pythonCode) return;
    const msg = modifyPrompt.trim();
    setModifyPrompt('');
    setModifying(true);
    setError(null);

    // Append user message immediately
    setChatHistory((prev) => [...prev, { role: 'user', text: msg }]);

    try {
      const res = await modifyPart(scriptId, pythonCode, partName || 'Part', msg, parameters);
      applyPartResponse(res);
      // Append assistant success message
      setChatHistory((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: `✅ Applied: "${msg}" — Part updated to ${res.part_name}.`,
          model: res.model_used,
        },
      ]);
    } catch (err) {
      console.error('[Modify error]', err);
      const detail = err.response?.data?.detail;
      const msg2 = typeof detail === 'string' ? detail : (detail?.error || err.message || 'Modification failed.');
      setError(`Modify error: ${msg2}`);
      setChatHistory((prev) => [
        ...prev,
        { role: 'assistant', text: `❌ Failed: ${msg2}`, isError: true },
      ]);
    } finally {
      setModifying(false);
      // Scroll chat to bottom
      setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
    }
  };

  // Slider change -> fast /api/recompute (<200ms)
  const handleParamChange = useCallback((name, value) => {
    setParamValues((prev) => {
      const nextValues = { ...prev, [name]: value };

      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);

      debounceTimerRef.current = setTimeout(async () => {
        if (!scriptId || !pythonCode) return;
        setRecomputing(true);

        try {
          const res = await recomputePart(scriptId, pythonCode, nextValues);
          setMeshUrl(res.mesh_url);
          setStepUrl(res.step_url);
          setMeshInfo(res.mesh_info || {});
          setRecompTime(res.recomputation_time_ms);
          setError(null);
        } catch (err) {
          console.error('[Recompute error]', err);
          const detail = err.response?.data?.detail;
          const msg = typeof detail === 'string' ? detail : (detail?.error || err.message || 'Recomputation failed.');
          setError(`Recomputation error: ${msg}`);
        } finally {
          setRecomputing(false);
        }
      }, 120); // 120ms debounce for silky smooth updates

      return nextValues;
    });
  }, [scriptId, pythonCode]);

  return (
    <div className="app-shell">
      {/* ── HEADER ──────────────────────────────────────────────── */}
      <header className="header">
        <div className="header-logo">
          <span>⚙️</span>
          <span>AI CAD Workbench</span>
          <span className="header-badge">WEEK 7 — CHAT-TO-MODIFY</span>
        </div>

        <div className="header-actions">
          <span className="status-pill" style={{ color: backendStatus === 'online' ? '#059669' : '#dc2626' }}>
            ● Backend {backendStatus}
          </span>
        </div>
      </header>

      {/* ── SIDEBAR ─────────────────────────────────────────────── */}
      <aside className="sidebar">
        {/* Prompt Input Section */}
        <div className="sidebar-section">
          <div className="sidebar-label">Natural Language Prompt</div>
          <div className="prompt-area">
            <textarea
              id="prompt-input"
              className="prompt-textarea"
              placeholder="e.g. A mounting bracket with four M5 corner holes..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                  e.preventDefault();
                  if (!loading && prompt.trim()) handleGenerate();
                }
              }}
            />

            <button
              id="btn-generate"
              className="generate-btn"
              onClick={() => handleGenerate()}
              disabled={loading || !prompt.trim()}
            >
              {loading ? (
                <>
                  <div className="spinner" />
                  <span>RAG + Generating CAD...</span>
                </>
              ) : (
                <>
                  <span>✨ Generate 3D Part</span>
                </>
              )}
            </button>
          </div>

          {/* Quick preset chips */}
          <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <span className="sidebar-label" style={{ marginBottom: 0 }}>Try an example</span>
            {PRESET_PROMPTS.slice(0, 3).map((p, idx) => (
              <button
                key={idx}
                className="preset-chip"
                onClick={() => {
                  setPrompt(p);
                  handleGenerate(p);
                }}
              >
                ⚡ {p}
              </button>
            ))}
          </div>
        </div>

        {/* Parameters Sliders Section */}
        <div className="params-scroll">
          <div className="sidebar-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Parametric Controls {recomputing && <span style={{ color: 'var(--accent-purple)', marginLeft: '6px' }}>(updating...)</span>}</span>
            {parameters.length > 0 && (
              <button
                className="preset-chip"
                style={{ padding: '3px 8px', fontSize: '10px' }}
                onClick={() => {
                  const resetVals = {};
                  parameters.forEach(p => { resetVals[p.name] = p.default; });
                  setParamValues(resetVals);
                }}
                title="Reset all sliders to initial defaults"
              >
                ↺ Reset All
              </button>
            )}
          </div>

          {parameters.length === 0 ? (
            <div className="no-params-msg">
              Generate a part to unlock real-time parametric sliders.
            </div>
          ) : (
            parameters.map((p) => (
              <ParameterSlider
                key={p.name}
                param={p}
                value={paramValues[p.name] ?? p.default}
                onChange={handleParamChange}
              />
            ))
          )}
        </div>

        {/* Model Metrics Footer */}
        {scriptId && (
          <div className="model-info">
            <div className="info-row">
              <span className="info-key">Script ID</span>
              <span className="info-val">{scriptId}</span>
            </div>
            <div className="info-row">
              <span className="info-key">AI Model</span>
              <span className="info-val accent">{modelUsed || 'build123d RAG'}</span>
            </div>
            <div className="info-row">
              <span className="info-key">Recompute Time</span>
              <span className="info-val success">{recompTime} ms</span>
            </div>
          </div>
        )}

        {/* ── CHAT-TO-MODIFY PANEL ─────────────────────────────── */}
        {scriptId && (
          <div className="chat-panel">
            <div className="sidebar-label" style={{ marginBottom: '10px' }}>
              💬 Chat to Modify
              <span style={{ fontFamily: 'var(--font-sans)', fontSize: '11px', fontWeight: 500, color: 'var(--text-secondary)', marginLeft: '8px' }}>
                Refine the part with natural language
              </span>
            </div>

            {/* Chat History */}
            {chatHistory.length > 0 && (
              <div className="chat-history">
                {chatHistory.map((msg, i) => (
                  <div
                    key={i}
                    className={`chat-bubble chat-bubble--${msg.role}${msg.isError ? ' chat-bubble--error' : ''}`}
                  >
                    <span className="chat-bubble-role">{msg.role === 'user' ? '👤 You' : '🤖 AI'}</span>
                    <span className="chat-bubble-text">{msg.text}</span>
                    {msg.model && (
                      <span className="chat-bubble-meta">{msg.model}</span>
                    )}
                  </div>
                ))}
                <div ref={chatEndRef} />
              </div>
            )}

            {/* Chat Input */}
            <div className="chat-input-row">
              <textarea
                className="chat-textarea"
                placeholder='e.g. "Make the walls 2mm thicker" or "Add a chamfer to top edges"'
                value={modifyPrompt}
                rows={2}
                onChange={(e) => setModifyPrompt(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                    e.preventDefault();
                    handleModify();
                  }
                }}
                disabled={modifying}
              />
              <button
                className="chat-send-btn"
                onClick={handleModify}
                disabled={modifying || !modifyPrompt.trim()}
                title="Send modification request (Ctrl+Enter)"
              >
                {modifying ? (
                  <><div className="spinner" style={{ width: '12px', height: '12px' }} /> Modifying...</>
                ) : '✨ Apply'}
              </button>
            </div>
          </div>
        )}
      </aside>

      {/* ── VIEWER AREA ────────────────────────────────────────── */}
      <main className="viewer-area">
        {/* Floating Part Name Badge */}
        {partName && (
          <div className="part-name-badge">
            {partName}
            {description && <span className="part-desc">{description}</span>}
          </div>
        )}

        {/* Download & View Controls Toolbar */}
        {meshUrl && (
          <div className="viewer-toolbar">
            <button
              onClick={() => setWireframe(!wireframe)}
              className="toolbar-btn"
              title="Toggle Mesh Wireframe Mode"
            >
              {wireframe ? '🟦 Solid Mode' : '🌐 Wireframe'}
            </button>
            {pythonCode && (
              <button
                onClick={() => setShowCodeModal(true)}
                className="toolbar-btn"
                title="Inspect Generated Python CAD Script"
              >
                💻 Python Code
              </button>
            )}
            <button
              onClick={() => viewerRef.current?.resetView()}
              className="toolbar-btn"
              title="Reset 3D Camera View"
            >
              🎥 Reset View
            </button>
            <a
              id="btn-download-stl"
              href={fileUrl(meshUrl)}
              download={`${partName || 'part'}.stl`}
              className="toolbar-btn"
            >
              📥 STL
            </a>
            {stepUrl && (
              <a
                id="btn-download-step"
                href={fileUrl(stepUrl)}
                download={`${partName || 'part'}.step`}
                className="toolbar-btn"
              >
                📐 STEP
              </a>
            )}
          </div>
        )}

        {/* 3D WebGL Canvas */}
        <Viewer3D ref={viewerRef} meshUrl={meshUrl} wireframe={wireframe} loading={loading} />

        {/* Empty State Overlay */}
        {!meshUrl && !loading && (
          <div className="viewer-empty">
            <div className="viewer-empty-card">
              <div className="viewer-empty-icon">🧊</div>
              <div className="viewer-empty-title">Interactive 3D Workbench</div>
              <div className="viewer-empty-sub">
                Enter a natural language description on the left panel or select an example preset to generate parametric 3D CAD geometry.
              </div>
            </div>
          </div>
        )}

        {/* Loading Overlay */}
        {loading && (
          <div className="loading-overlay">
            <div className="loading-card">
              <div className="spinner" style={{ width: '28px', height: '28px' }} />
              <div className="loading-title">Retrieving RAG Examples & Building Solid Geometry...</div>
              <div className="loading-dots">
                <div className="loading-dot" />
                <div className="loading-dot" />
                <div className="loading-dot" />
              </div>
            </div>
          </div>
        )}

        {/* Error Banner */}
        {error && (
          <div className="error-banner">
            ⚠️ {error}
          </div>
        )}

        {/* Mesh Metrics Floating Bar */}
        {meshInfo && meshInfo.dimensions_mm && (
          <div className="mesh-stats">
            <div className="mesh-stat">
              <span className="mesh-stat-val">{meshInfo.dimensions_mm.x} × {meshInfo.dimensions_mm.y} × {meshInfo.dimensions_mm.z}</span>
              <span className="mesh-stat-key">Bounding (mm)</span>
            </div>
            {meshInfo.volume_mm3 && (
              <div className="mesh-stat">
                <span className="mesh-stat-val">{(meshInfo.volume_mm3 / 1000).toFixed(1)} cm³</span>
                <span className="mesh-stat-key">Volume</span>
              </div>
            )}
          </div>
        )}

        {/* Python Code Inspection Modal */}
        {showCodeModal && pythonCode && (
          <div className="modal-backdrop" onClick={() => setShowCodeModal(false)}>
            <div className="modal-card" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <span className="modal-title">💻 Generated build123d Python Script ({scriptId})</span>
                <button className="modal-close-btn" onClick={() => setShowCodeModal(false)}>✕</button>
              </div>
              <pre className="modal-code"><code>{pythonCode}</code></pre>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button
                  className="toolbar-btn"
                  onClick={() => {
                    navigator.clipboard.writeText(pythonCode);
                    alert('Python CAD code copied to clipboard!');
                  }}
                >
                  📋 Copy Code
                </button>
                <button className="toolbar-btn" onClick={() => setShowCodeModal(false)}>
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
