import React from 'react';

/**
 * ChatModifyPanel — Conversational CAD refinement interface with quick action pills and streaming delta feedback.
 */
export default function ChatModifyPanel({
  scriptId,
  activeTab,
  chatHistory,
  chatEndRef,
  modifyPrompt,
  setModifyPrompt,
  modifying,
  handleModify,
  QUICK_MODIFICATIONS,
}) {
  if (!scriptId || (activeTab !== 'all' && activeTab !== 'chat')) {
    return null;
  }

  return (
    <div className={`chat-panel bento-card ${activeTab === 'chat' ? 'bento-card--full' : ''}`}>
      <div className="section-header">
        <span className="section-title">Chat-to-Modify</span>
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
                <span>{msg.role === 'user' ? 'Designer' : 'CAD Kernel'}</span>
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
          aria-label="CAD modification request"
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
          ) : (
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="9 18 15 12 9 6"/>
              </svg>
              <span>Apply</span>
            </span>
          )}
        </button>
      </div>
    </div>
  );
}
