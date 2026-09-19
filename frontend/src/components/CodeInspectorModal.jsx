import React from 'react';

/**
 * CodeInspectorModal — Dialog for viewing and copying the generated Python CAD build123d script.
 */
export default function CodeInspectorModal({
  isOpen,
  onClose,
  pythonCode,
  partName,
  scriptId,
  onError,
}) {
  if (!isOpen || !pythonCode) return null;

  const handleCopy = async () => {
    try {
      if (!navigator.clipboard) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(pythonCode);
      alert('Python CAD code copied to clipboard!');
    } catch {
      onError?.('Clipboard access was denied. Select and copy the code manually.');
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="code-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <div className="modal-title-group">
            <span className="modal-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="16 18 22 12 16 6"/>
                <polyline points="8 6 2 12 8 18"/>
              </svg>
            </span>
            <div>
              <div className="modal-title" id="code-modal-title">build123d Python Script ({scriptId})</div>
              <div className="modal-subtitle">Runtime build123d script with injected export paths</div>
            </div>
          </div>
          <button
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close code inspector"
            autoFocus
          >
            ✕
          </button>
        </div>

        <pre className="modal-code"><code>{pythonCode}</code></pre>

        <div className="modal-footer">
          <span className="modal-hint">All parameters are exposed in the PARAMS dict at the top of the script.</span>
          <div className="modal-actions">
            <button
              className="toolbar-btn export-btn"
              onClick={handleCopy}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
              </svg>
              <span>Copy Code</span>
            </button>
            <button className="toolbar-btn" onClick={onClose}>
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
