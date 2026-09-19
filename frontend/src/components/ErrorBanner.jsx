import React from 'react';

/**
 * ErrorBanner — Displays system or execution errors with dismiss action.
 */
export default function ErrorBanner({ error, onDismiss }) {
  if (!error) return null;

  return (
    <div className="error-banner">
      <span className="error-icon">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
      </span>
      <div className="error-msg">{error}</div>
      <button className="error-dismiss" onClick={onDismiss} aria-label="Dismiss error">
        ✕
      </button>
    </div>
  );
}
