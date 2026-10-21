import React, { useRef, useState } from 'react';

/**
 * PromptPanel — Natural Language CAD input panel, quick-launch presets,
 * and Sketch-to-CAD upload zone.
 */
export default function PromptPanel({
  prompt,
  setPrompt,
  loading,
  handleGenerate,
  PRESET_CATEGORIES,
  // Sketch-to-CAD props
  onSketchFile,
  sketchFile,
  sketchLoading,
  handleSketchGenerate,
}) {
  const fileInputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);

  // --- Drag-and-drop handlers ---
  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };
  const handleDragLeave = () => setDragOver(false);
  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file && /^image\/(png|jpeg|webp)$/.test(file.type)) {
      onSketchFile(file);
    }
  };
  const handleFileChange = (e) => {
    const file = e.target.files?.[0] ?? null;
    onSketchFile(file);
    // Reset so selecting same file again triggers onChange
    e.target.value = '';
  };

  const sketchPreviewUrl = sketchFile ? URL.createObjectURL(sketchFile) : null;
  const isAnyLoading = loading || sketchLoading;

  return (
    <div className="sidebar-section bento-card">
      <div className="section-header">
        <span className="section-title">Natural Language Prompt</span>
        <span className="section-tag">RAG + LLM</span>
      </div>

      <div className="prompt-area">
        <textarea
          id="prompt-input"
          aria-label="Natural language CAD prompt"
          className="prompt-textarea"
          placeholder="e.g. A mounting plate 100x60x5mm with four M4 corner clearance holes and 5mm edge fillets..."
          value={prompt}
          disabled={sketchLoading}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
              e.preventDefault();
              if (!isAnyLoading && prompt.trim()) handleGenerate();
            }
          }}
        />

        <button
          id="btn-generate"
          className="generate-btn"
          onClick={() => handleGenerate()}
          disabled={isAnyLoading || !prompt.trim()}
          title="Generate parametric solid (G)"
        >
          {loading ? (
            <>
              <div className="spinner" />
              <span>RAG Synthesizing Solid...</span>
            </>
          ) : (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
              </svg>
              <span>Generate Parametric 3D Solid</span>
            </>
          )}
        </button>
      </div>

      {/* ── Sketch-to-CAD Upload Zone ────────────────────────────────────── */}
      <div className="sketch-section">
        <div className="sketch-divider">
          <span className="sketch-divider-label">or upload a sketch</span>
        </div>

        {sketchFile ? (
          /* ── Sketch Preview State ── */
          <div className="sketch-preview-card">
            <img
              src={sketchPreviewUrl}
              alt="Sketch preview"
              className="sketch-preview-img"
            />
            <div className="sketch-preview-info">
              <span className="sketch-preview-name" title={sketchFile.name}>
                {sketchFile.name.length > 24
                  ? `${sketchFile.name.slice(0, 22)}…`
                  : sketchFile.name}
              </span>
              <span className="sketch-preview-size">
                {(sketchFile.size / 1024).toFixed(0)} KB
              </span>
            </div>
            <button
              className="sketch-clear-btn"
              onClick={() => onSketchFile(null)}
              title="Remove sketch"
              aria-label="Remove sketch"
            >
              ✕
            </button>
          </div>
        ) : (
          /* ── Drop Zone ── */
          <div
            id="sketch-upload-zone"
            className={`sketch-upload-zone${dragOver ? ' drag-over' : ''}`}
            role="button"
            tabIndex={0}
            aria-label="Upload a mechanical sketch image"
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            onKeyDown={(e) => e.key === 'Enter' && fileInputRef.current?.click()}
          >
            <svg
              className="sketch-upload-icon"
              width="20" height="20" viewBox="0 0 24 24"
              fill="none" stroke="currentColor" strokeWidth="2"
              strokeLinecap="round" strokeLinejoin="round"
            >
              <polyline points="16 16 12 12 8 16"/>
              <line x1="12" y1="12" x2="12" y2="21"/>
              <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/>
            </svg>
            <span className="sketch-upload-label">
              Drop a sketch here or <u>browse</u>
            </span>
            <span className="sketch-upload-hint">PNG · JPEG · WEBP · max 10 MB</span>
            <input
              ref={fileInputRef}
              id="sketch-file-input"
              type="file"
              accept="image/png,image/jpeg,image/webp"
              style={{ display: 'none' }}
              onChange={handleFileChange}
            />
          </div>
        )}

        {/* ── Analyze button — only shown when a file is selected ── */}
        {sketchFile && (
          <>
            <button
              id="btn-sketch-generate"
              className="sketch-analyze-btn"
              onClick={handleSketchGenerate}
              disabled={isAnyLoading}
              title="Parse sketch with Gemini Vision and generate 3D model"
            >
              {sketchLoading ? (
                <>
                  <div className="spinner" />
                  <span>Parsing Sketch…</span>
                </>
              ) : (
                <>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  </svg>
                  <span>Analyze Sketch &amp; Generate 3D Model</span>
                </>
              )}
            </button>
            {prompt && prompt.trim() && (
              <div className="sketch-prompt-hint">
                Guidance attached: &ldquo;{prompt.trim().slice(0, 48)}{prompt.trim().length > 48 ? '…' : ''}&rdquo;
              </div>
            )}
          </>
        )}
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
                disabled={isAnyLoading}
              >
                <span className="preset-chip-dot" />
                <span>{item.label}</span>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
