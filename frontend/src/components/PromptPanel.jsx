import React from 'react';

/**
 * PromptPanel — Natural Language CAD input panel and quick launch presets.
 */
export default function PromptPanel({
  prompt,
  setPrompt,
  loading,
  handleGenerate,
  PRESET_CATEGORIES,
}) {
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
