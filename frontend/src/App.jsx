/**
 * App.jsx — AI-Driven Parametric CAD Workbench
 *
 * Design System: Technical Neobrutalist Bento (Tilda-inspired)
 *  - Bento Grid layout partitioning Viewport, Sliders, Telemetry HUD, and Chat-to-Modify
 *  - High-contrast 2.5px solid borders with 4px hard drop shadows
 *  - Floating 3D viewport controls: Top / Front / Side / Isometric camera presets
 *  - PBR Material switcher (Machined Aluminum, CAD Blue, Tooling Yellow, Carbon Slate)
 *  - Real-time parametric slider recompute (<200ms) with debounce
 *  - Chat-to-Modify conversational engineering loop
 *  - Telemetry HUD: Watertight Manifold, Solid Body Count, Bounding Envelope, Volume
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import Viewer3D, { MATERIAL_PRESETS } from './components/Viewer3D';
import ParameterSlider from './components/ParameterSlider';
import { generatePart, recomputePart, healthCheck, modifyPart } from './api';

// Build a full URL for file downloads / static assets
const fileUrl = (path) => {
  if (!path) return null;
  const baseUrl = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '');
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${baseUrl}${cleanPath}`;
};

// Categorized Preset CAD Prompts
const PRESET_CATEGORIES = [
  {
    category: 'Mechanical',
    icon: '⚙️',
    prompts: [
      { label: 'Mounting Bracket', prompt: 'A mounting bracket with four M5 corner holes, 80x50x5mm with 4mm fillets' },
      { label: 'L-Bracket', prompt: 'An L-bracket with two perpendicular 60mm arms, 4mm thickness, and M4 mounting holes' },
      { label: 'Flanged Bushing', prompt: 'A flanged bushing with 12mm inner bore, 24mm outer diameter, and 30mm flange' }
    ]
  },
  {
    category: 'Drones & Robotics',
    icon: '🛸',
    prompts: [
      { label: 'Quadcopter Frame', prompt: 'A quadcopter drone central chassis plate with 4 diagonal motor arms and M3 motor mounts' },
      { label: 'Hybrid Flying Car', prompt: 'A hybrid RC flying car chassis 400x280x4mm with 4 motor arms, battery bay, and wheel mounts' }
    ]
  },
  {
    category: 'Enclosures',
    icon: '📦',
    prompts: [
      { label: 'PCB Enclosure', prompt: 'A rectangular electronics enclosure box 75x50x25mm with 2mm wall thickness and mounting standoffs' },
      { label: 'Hollow Cylinder', prompt: 'A hollow cylinder with 25mm outer radius, 3mm wall thickness, and 50mm height' }
    ]
  }
];

const QUICK_MODIFICATIONS = [
  'Make walls 2mm thicker',
  'Add 4x M3 corner mounting holes',
  'Add 3mm fillets to all vertical edges',
  'Increase overall length by 20mm'
];

export default function App() {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [recomputing, setRecomputing] = useState(false);
  const [error, setError] = useState(null);

  // Response state from /api/generate & /api/modify
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

  // Viewport Control States
  const [wireframe, setWireframe] = useState(false);
  const [showAxes, setShowAxes] = useState(true);
  const [materialType, setMaterialType] = useState('blue');
  const [activeCamView, setActiveCamView] = useState('iso');
  const [showCodeModal, setShowCodeModal] = useState(false);
  const viewerRef = useRef(null);

  // Chat-to-Modify state
  const [chatHistory, setChatHistory] = useState([]);
  const [modifyPrompt, setModifyPrompt] = useState('');
  const [modifying, setModifying] = useState(false);
  const chatEndRef = useRef(null);

  // Model undo history — stores last 5 snapshots for undo
  const [modelHistory, setModelHistory] = useState([]);
  const [showDimensions, setShowDimensions] = useState(true);

  // Debounce timer for slider recomputation
  const debounceTimerRef = useRef(null);

  // Health check on mount + debounce timer cleanup
  useEffect(() => {
    healthCheck()
      .then((data) => setBackendStatus(data.status === 'online' ? 'online' : 'offline'))
      .catch(() => setBackendStatus('offline'));

    return () => {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    };
  }, []);

  // Sidebar active tab ('sliders' | 'chat' | 'prompt' | 'all')
  const [activeTab, setActiveTab] = useState('all');

  // Apply response from generate or modify
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
    // Switch to sliders view if parameters are present so they have 100% space
    if (res.parameters && res.parameters.length > 0) {
      setActiveTab('sliders');
    }
  };

  // Submit prompt -> /api/generate
  const handleGenerate = async (overridePrompt) => {
    const activePrompt = overridePrompt || prompt;
    if (!activePrompt.trim() || loading) return;

    setLoading(true);
    setError(null);
    setChatHistory([]);

    try {
      const res = await generatePart(activePrompt);
      applyPartResponse(res);
    } catch (err) {
      console.error('[Generate error]', err);
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : (detail?.error || err.message || 'Generation failed. Check backend log.'));
    } finally {
      setLoading(false);
    }
  };

  // Capture snapshot for undo stack
  const saveSnapshot = () => {
    if (!scriptId || !pythonCode) return;
    setModelHistory((prev) => [
      {
        scriptId,
        partName,
        description,
        pythonCode,
        parameters: [...parameters],
        paramValues: { ...paramValues },
        meshUrl,
        stepUrl,
        meshInfo,
        recompTime,
        modelUsed,
      },
      ...prev,
    ].slice(0, 5));
  };

  // Undo to previous model state
  const handleUndo = () => {
    if (modelHistory.length === 0) return;
    const [lastState, ...remaining] = modelHistory;
    setModelHistory(remaining);
    setScriptId(lastState.scriptId);
    setPartName(lastState.partName);
    setDescription(lastState.description);
    setPythonCode(lastState.pythonCode);
    setParameters(lastState.parameters || []);
    setParamValues(lastState.paramValues || {});
    setMeshUrl(lastState.meshUrl);
    setStepUrl(lastState.stepUrl);
    setMeshInfo(lastState.meshInfo || {});
    setRecompTime(lastState.recompTime);
    setModelUsed(lastState.modelUsed);
  };

  // Chat-to-Modify -> /api/modify
  const handleModify = async (overrideMsg) => {
    const msg = (overrideMsg || modifyPrompt).trim();
    if (!msg || modifying || !scriptId || !pythonCode) return;
    setModifyPrompt('');
    setModifying(true);
    setError(null);

    setChatHistory((prev) => [...prev, { role: 'user', text: msg }]);

    try {
      saveSnapshot();
      const res = await modifyPart(scriptId, pythonCode, partName || 'Part', msg, parameters);
      applyPartResponse(res);
      setChatHistory((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: `✅ Applied: "${msg}" — Updated solid model.`,
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
      }, 120);

      return nextValues;
    });
  }, [scriptId, pythonCode]);

  // Reset all sliders to defaults AND trigger recompute on canvas
  const handleResetAll = async () => {
    if (!parameters.length || !scriptId || !pythonCode) return;
    const resetVals = {};
    parameters.forEach((p) => { resetVals[p.name] = p.default; });
    setParamValues(resetVals);
    setRecomputing(true);
    try {
      const res = await recomputePart(scriptId, pythonCode, resetVals);
      setMeshUrl(res.mesh_url);
      setStepUrl(res.step_url);
      setMeshInfo(res.mesh_info || {});
      setRecompTime(res.recomputation_time_ms);
      setError(null);
    } catch (err) {
      console.error('[Reset error]', err);
    } finally {
      setRecomputing(false);
    }
  };

  const handleCameraPreset = (view) => {
    setActiveCamView(view);
    viewerRef.current?.setCameraView(view);
  };

  return (
    <div className="app-shell">
      {/* ── BENTO HEADER ─────────────────────────────────────────── */}
      <header className="header">
        <div className="header-logo">
          <div className="header-logo-icon">🧊</div>
          <div>
            <div className="header-title">AI Parametric CAD Workbench</div>
            <div className="header-subtitle">build123d B-Rep Solid Modeling Kernel</div>
          </div>
          <span className="header-badge">ENGINEERING SPEC V2.0</span>
        </div>

        <div className="header-actions">
          {modelHistory.length > 0 && (
            <button
              className="toolbar-btn header-action-btn"
              onClick={handleUndo}
              title={`Undo to previous model state (${modelHistory.length} in stack)`}
              style={{ background: 'var(--accent-pink)' }}
            >
              ↺ Undo ({modelHistory.length})
            </button>
          )}
          {pythonCode && (
            <button
              className="toolbar-btn header-action-btn"
              onClick={() => setShowCodeModal(true)}
              title="Inspect Python CAD Script"
            >
              💻 Inspect Code
            </button>
          )}
          <div className="status-pill" style={{ borderColor: backendStatus === 'online' ? '#10B981' : '#EF4444' }}>
            <span
              className="status-dot"
              style={{ background: backendStatus === 'online' ? '#10B981' : '#EF4444' }}
            />
            <span>{backendStatus === 'online' ? 'CAD Engine Online' : 'Connecting...'}</span>
          </div>
        </div>
      </header>

      {/* ── LEFT BENTO SIDEBAR: CONTROLS & CHAT ──────────────────── */}
      <aside className="sidebar">
        {/* Sidebar Mode Tabs */}
        <div className="sidebar-tabs-nav">
          <button
            type="button"
            className={`sidebar-tab-btn ${activeTab === 'sliders' ? 'active' : ''}`}
            onClick={() => setActiveTab('sliders')}
          >
            ⚙️ Sliders {parameters.length > 0 && <span className="tab-count-badge">{parameters.length}</span>}
          </button>
          <button
            type="button"
            className={`sidebar-tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
            disabled={!scriptId}
          >
            💬 Chat Modify {chatHistory.length > 0 && <span className="tab-count-badge">{chatHistory.length}</span>}
          </button>
          <button
            type="button"
            className={`sidebar-tab-btn ${activeTab === 'prompt' ? 'active' : ''}`}
            onClick={() => setActiveTab('prompt')}
          >
            ⚡ New Part
          </button>
          <button
            type="button"
            className={`sidebar-tab-btn ${activeTab === 'all' ? 'active' : ''}`}
            onClick={() => setActiveTab('all')}
            title="Show all sections stacked"
          >
            📑 All
          </button>
        </div>

        {/* Prompt Input Section */}
        {(activeTab === 'all' || activeTab === 'prompt' || !scriptId) && (
          <div className="sidebar-section bento-card">
            <div className="section-header">
              <span className="section-title">💬 Natural Language Prompt</span>
              <span className="section-tag">RAG + LLM</span>
            </div>

            <div className="prompt-area">
              <textarea
                id="prompt-input"
                className="prompt-textarea"
                placeholder="e.g. A mounting plate 100x60x5mm with four M4 corner clearance holes and 5mm edge fillets..."
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
                    <span>RAG Retrieving & Synthesizing Solid...</span>
                  </>
                ) : (
                  <>
                    <span>⚡ Generate Parametric 3D Solid</span>
                  </>
                )}
              </button>
            </div>

            {/* Categorized Quick Presets */}
            <div className="presets-container">
              <div className="preset-tabs-label">Quick Launch Presets:</div>
              <div className="preset-pills-list">
                {PRESET_CATEGORIES.map((cat) =>
                  cat.prompts.map((item, idx) => (
                    <button
                      key={`${cat.category}-${idx}`}
                      className="preset-chip"
                      onClick={() => {
                        setPrompt(item.prompt);
                        handleGenerate(item.prompt);
                      }}
                      title={item.prompt}
                    >
                      {cat.icon} {item.label}
                    </button>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* Parametric Sliders Section */}
        {(activeTab === 'all' || activeTab === 'sliders') && (
          <div className={`params-scroll bento-card ${activeTab === 'sliders' ? 'bento-card--full' : ''}`}>
            <div className="section-header">
              <div className="section-title">
                ⚙️ Parametric Dimensions
                {parameters.length > 0 && (
                  <span className="section-tag">{parameters.length} Variables</span>
                )}
                {recomputing && <span className="recomputing-tag">Updating...</span>}
              </div>
              {parameters.length > 0 && (
                <button
                  className="preset-chip reset-chip"
                  onClick={handleResetAll}
                  title="Reset all sliders to default dimensions"
                >
                  ↺ Reset All
                </button>
              )}
            </div>

            {parameters.length === 0 ? (
              <div className="no-params-msg">
                <div className="empty-sliders-icon">📐</div>
                <div>Generate a model to unlock real-time build123d parametric sliders.</div>
                <button
                  className="preset-chip"
                  style={{ marginTop: '8px' }}
                  onClick={() => setActiveTab('prompt')}
                >
                  ⚡ Choose a Prompt or Preset
                </button>
              </div>
            ) : (
              <div className="sliders-list">
                {parameters.map((p) => (
                  <ParameterSlider
                    key={p.name}
                    param={p}
                    value={paramValues[p.name] ?? p.default}
                    onChange={handleParamChange}
                  />
                ))}
              </div>
            )}

            {/* Quick Modify Shortcut Bar at bottom of Sliders */}
            {scriptId && (
              <div className="slider-bottom-quick-bar">
                <div className="quick-bar-label">⚡ Quick Delta Actions:</div>
                <div className="quick-mods-bar">
                  {QUICK_MODIFICATIONS.slice(0, 3).map((qm, i) => (
                    <button
                      key={i}
                      className="quick-mod-btn"
                      onClick={() => {
                        setActiveTab('chat');
                        handleModify(qm);
                      }}
                      disabled={modifying}
                    >
                      + {qm}
                    </button>
                  ))}
                  <button
                    className="quick-mod-btn quick-mod-btn--chat"
                    onClick={() => setActiveTab('chat')}
                  >
                    💬 Open Chat to Modify →
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Chat-to-Modify Section */}
        {scriptId && (activeTab === 'all' || activeTab === 'chat') && (
          <div className={`chat-panel bento-card ${activeTab === 'chat' ? 'bento-card--full' : ''}`}>
            <div className="section-header">
              <span className="section-title">💬 Chat-to-Modify</span>
              <span className="section-tag">Conversational Delta</span>
            </div>

            {/* Quick Modification Pills */}
            <div className="quick-mods-bar">
              {QUICK_MODIFICATIONS.map((qm, i) => (
                <button
                  key={i}
                  className="quick-mod-btn"
                  onClick={() => handleModify(qm)}
                  disabled={modifying}
                >
                  + {qm}
                </button>
              ))}
            </div>

            {/* Chat Conversation History */}
            {chatHistory.length > 0 && (
              <div className="chat-history">
                {chatHistory.map((msg, i) => (
                  <div
                    key={i}
                    className={`chat-bubble chat-bubble--${msg.role}${msg.isError ? ' chat-bubble--error' : ''}`}
                  >
                    <div className="chat-bubble-header">
                      <span>{msg.role === 'user' ? '👤 Designer' : '🤖 CAD Engine'}</span>
                      {msg.model && <span className="chat-bubble-meta">{msg.model}</span>}
                    </div>
                    <div className="chat-bubble-text">{msg.text}</div>
                  </div>
                ))}
                <div ref={chatEndRef} />
              </div>
            )}

            {/* Modification Input */}
            <div className="chat-input-row">
              <textarea
                className="chat-textarea"
                placeholder='e.g. "Increase flange radius by 5mm" or "Add 2mm chamfer"'
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
                onClick={() => handleModify()}
                disabled={modifying || !modifyPrompt.trim()}
                title="Apply modification (Ctrl+Enter)"
              >
                {modifying ? (
                  <div className="spinner" style={{ width: '14px', height: '14px' }} />
                ) : '✨ Modify'}
              </button>
            </div>
          </div>
        )}
      </aside>

      {/* ── MAIN 3D CAD VIEWPORT & HUD ───────────────────────────── */}
      <main className="viewer-area">
        {/* Floating Part Title & Description Banner */}
        {partName && (
          <div className="part-name-badge">
            <div className="part-name-text">
              <span className="part-icon">🧊</span>
              <span>{partName}</span>
            </div>
            {description && <div className="part-desc">{description}</div>}
          </div>
        )}

        {/* Viewport Top Floating Controls Toolbar */}
        {meshUrl && (
          <div className="viewer-toolbar">
            {/* Camera View Angle Presets */}
            <div className="toolbar-group">
              <span className="toolbar-group-label">Camera:</span>
              <button
                className={`cam-btn ${activeCamView === 'iso' ? 'active' : ''}`}
                onClick={() => handleCameraPreset('iso')}
                title="Isometric View"
              >
                ISO
              </button>
              <button
                className={`cam-btn ${activeCamView === 'top' ? 'active' : ''}`}
                onClick={() => handleCameraPreset('top')}
                title="Top View (XY Plane)"
              >
                TOP
              </button>
              <button
                className={`cam-btn ${activeCamView === 'front' ? 'active' : ''}`}
                onClick={() => handleCameraPreset('front')}
                title="Front View (XZ Plane)"
              >
                FRONT
              </button>
              <button
                className={`cam-btn ${activeCamView === 'side' ? 'active' : ''}`}
                onClick={() => handleCameraPreset('side')}
                title="Side View (YZ Plane)"
              >
                SIDE
              </button>
              <button
                className="cam-btn"
                onClick={() => viewerRef.current?.resetView()}
                title="Fit Mesh to Viewport"
              >
                FIT
              </button>
            </div>

            {/* Material Presets Selector */}
            <div className="toolbar-group">
              <span className="toolbar-group-label">Material:</span>
              {Object.entries(MATERIAL_PRESETS).map(([key, mat]) => (
                <button
                  key={key}
                  className={`material-btn ${materialType === key ? 'active' : ''}`}
                  onClick={() => setMaterialType(key)}
                  title={mat.name}
                >
                  <span>{mat.icon}</span>
                  <span className="mat-btn-label">{mat.name.split(' ')[0]}</span>
                </button>
              ))}
            </div>

            {/* Render Mode & Helpers */}
            <div className="toolbar-group">
              <button
                onClick={() => setWireframe(!wireframe)}
                className={`toolbar-btn ${wireframe ? 'active' : ''}`}
                title="Toggle Solid / Wireframe mesh mode"
              >
                {wireframe ? '🟦 Solid' : '🌐 Wireframe'}
              </button>
              <button
                onClick={() => setShowAxes(!showAxes)}
                className={`toolbar-btn ${showAxes ? 'active' : ''}`}
                title="Toggle XYZ coordinate axes"
              >
                🧭 Axes
              </button>
              <button
                onClick={() => setShowDimensions(!showDimensions)}
                className={`toolbar-btn ${showDimensions ? 'active' : ''}`}
                title="Toggle 3D Bounding Box Dimension Annotations (L × W × H)"
              >
                📏 Dims
              </button>
            </div>

            {/* Export CAD Files */}
            <div className="toolbar-group export-group">
              {meshUrl && (
                <a
                  id="btn-download-stl"
                  href={fileUrl(meshUrl)}
                  download={`${partName || 'part'}.stl`}
                  className="toolbar-btn export-btn"
                  title="Download 3D STL Triangle Mesh"
                >
                  📥 STL
                </a>
              )}
              {stepUrl && (
                <a
                  id="btn-download-step"
                  href={fileUrl(stepUrl)}
                  download={`${partName || 'part'}.step`}
                  className="toolbar-btn export-btn step-btn"
                  title="Download Solid STEP Boundary-Representation CAD File"
                >
                  📐 STEP
                </a>
              )}
            </div>
          </div>
        )}

        {/* 3D WebGL Canvas */}
        <Viewer3D
          ref={viewerRef}
          meshUrl={meshUrl}
          wireframe={wireframe}
          materialType={materialType}
          showAxes={showAxes}
          showDimensions={showDimensions}
        />

        {/* Empty Canvas Placeholder */}
        {!meshUrl && !loading && (
          <div className="viewer-empty">
            <div className="viewer-empty-card">
              <div className="viewer-empty-icon">🧊</div>
              <div className="viewer-empty-title">AI Parametric CAD Studio</div>
              <div className="viewer-empty-sub">
                Type a natural language mechanical description on the left or select a Quick Launch preset.
                The workbench synthesizes real OpenCASCADE boundary-representation geometry via <code>build123d</code>.
              </div>
              <div className="empty-features-grid">
                <div className="empty-feature-item">⚡ Sub-200ms Slider Recompute</div>
                <div className="empty-feature-item">📐 STEP & STL Dual Export</div>
                <div className="empty-feature-item">💬 Chat-to-Modify Loop</div>
                <div className="empty-feature-item">🛡️ AST Security Sandbox</div>
              </div>
            </div>
          </div>
        )}

        {/* Generation Loading Overlay */}
        {loading && (
          <div className="loading-overlay">
            <div className="loading-card">
              <div className="spinner loading-spinner-large" />
              <div className="loading-title">Synthesizing Solid B-Rep Geometry...</div>
              <div className="loading-sub">
                ChromaDB k-NN Retrieval ➔ LLM Code Synthesis ➔ Subprocess AST Execution ➔ Manifold Validation
              </div>
            </div>
          </div>
        )}

        {/* Error Banner */}
        {error && (
          <div className="error-banner">
            <span className="error-icon">⚠️</span>
            <div className="error-msg">{error}</div>
            <button className="error-dismiss" onClick={() => setError(null)}>✕</button>
          </div>
        )}

        {/* Engineering Telemetry & Mesh Metrics HUD */}
        {meshInfo && meshInfo.dimensions_mm && (
          <div className="mesh-stats">
            <div className="mesh-stat">
              <span className="mesh-stat-key">BOUNDING ENVELOPE</span>
              <span className="mesh-stat-val">
                {meshInfo.dimensions_mm.x} × {meshInfo.dimensions_mm.y} × {meshInfo.dimensions_mm.z} mm
              </span>
            </div>

            {meshInfo.volume_mm3 && (
              <div className="mesh-stat">
                <span className="mesh-stat-key">SOLID VOLUME</span>
                <span className="mesh-stat-val">{(meshInfo.volume_mm3 / 1000).toFixed(1)} cm³</span>
              </div>
            )}

            {meshInfo.is_watertight !== undefined && (
              <div className="mesh-stat">
                <span className="mesh-stat-key">TOPOLOGY</span>
                <span
                  className="mesh-stat-val status-badge"
                  style={{
                    background: meshInfo.is_watertight ? '#10B981' : '#EF4444',
                    color: '#FFFFFF'
                  }}
                >
                  {meshInfo.is_watertight ? '✓ Watertight' : 'Non-Manifold'}
                </span>
              </div>
            )}

            {recompTime !== null && (
              <div className="mesh-stat">
                <span className="mesh-stat-key">RECOMPUTE</span>
                <span className="mesh-stat-val accent">{recompTime} ms</span>
              </div>
            )}

            {modelUsed && (
              <div className="mesh-stat">
                <span className="mesh-stat-key">AI SYNTHESIS</span>
                <span className="mesh-stat-val">{modelUsed}</span>
              </div>
            )}
          </div>
        )}

        {/* Python CAD Script Code Inspector Modal */}
        {showCodeModal && pythonCode && (
          <div className="modal-backdrop" onClick={() => setShowCodeModal(false)}>
            <div className="modal-card" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <div className="modal-title-group">
                  <span className="modal-icon">💻</span>
                  <div>
                    <div className="modal-title">build123d Python Script ({scriptId})</div>
                    <div className="modal-subtitle">Directly executable in FreeCAD / CQ-Editor / Python Virtualenv</div>
                  </div>
                </div>
                <button className="modal-close-btn" onClick={() => setShowCodeModal(false)}>✕</button>
              </div>

              <pre className="modal-code"><code>{pythonCode}</code></pre>

              <div className="modal-footer">
                <span className="modal-hint">All parameters are exposed in the PARAMS dict at the top of the script.</span>
                <div className="modal-actions">
                  <button
                    className="toolbar-btn export-btn"
                    onClick={() => {
                      navigator.clipboard.writeText(pythonCode);
                      alert('Python CAD code copied to clipboard!');
                    }}
                  >
                    📋 Copy Python Code
                  </button>
                  <button className="toolbar-btn" onClick={() => setShowCodeModal(false)}>
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

