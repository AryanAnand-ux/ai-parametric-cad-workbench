import React, { useState } from 'react';

export default function ShareModal({ isOpen, onClose, scriptId, partName, meshUrl, stepUrl }) {
  const [copiedLink, setCopiedLink] = useState(false);
  const [copiedEmbed, setCopiedEmbed] = useState(false);

  if (!isOpen || !scriptId) return null;

  const shareUrl = `${window.location.origin}/#model=${scriptId}`;
  const embedCode = `<iframe src="${window.location.origin}/#embed=${scriptId}" width="800" height="600" frameborder="0" allowfullscreen></iframe>`;

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2000);
    } catch {
      alert('Please copy the URL manually.');
    }
  };

  const handleCopyEmbed = async () => {
    try {
      await navigator.clipboard.writeText(embedCode);
      setCopiedEmbed(true);
      setTimeout(() => setCopiedEmbed(false), 2000);
    } catch {
      alert('Please copy the embed code manually.');
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-card"
        style={{ maxWidth: '480px' }}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        {/* Atelier Header */}
        <div className="modal-header">
          <div className="modal-title-group">
            <span style={{ fontSize: '18px' }}>🔗</span>
            <div>
              <div className="modal-title">Share CAD Model</div>
              <div className="modal-subtitle">{partName || scriptId} — Atelier Link & Embed</div>
            </div>
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close dialog"
          >
            ✕
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '24px 28px', background: 'var(--bg-card)' }}>
          <p style={{ margin: '0 0 18px', fontSize: '13px', color: '#6B6363', lineHeight: 1.5 }}>
            Share <strong style={{ color: '#474040' }}>{partName || 'this parametric part'}</strong> with team members or embed interactive 3D solid inspection in your engineering documents.
          </p>

          {/* Share Link */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: '#6B6363', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Public Workspace Link
            </label>
            <div style={{ display: 'flex', gap: '6px' }}>
              <input
                type="text"
                readOnly
                value={shareUrl}
                style={{
                  flex: 1,
                  padding: '8px 12px',
                  background: '#F6F6F0',
                  border: '1px solid rgba(71, 64, 64, 0.2)',
                  borderRadius: '6px',
                  color: '#474040',
                  fontSize: '12px',
                  outline: 'none',
                  fontFamily: 'var(--font-mono)',
                }}
              />
              <button
                type="button"
                onClick={handleCopyLink}
                style={{
                  padding: '8px 14px',
                  background: copiedLink ? '#489235' : '#474040',
                  border: 'none',
                  borderRadius: '6px',
                  color: '#FFFDE2',
                  fontWeight: 600,
                  fontSize: '12px',
                  cursor: 'pointer',
                  transition: 'background 0.15s ease',
                  whiteSpace: 'nowrap',
                }}
              >
                {copiedLink ? 'Copied ✓' : 'Copy'}
              </button>
            </div>
          </div>

          {/* Embed Snippet */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: '#6B6363', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Embed 3D Viewer HTML
            </label>
            <div style={{ display: 'flex', gap: '6px' }}>
              <input
                type="text"
                readOnly
                value={embedCode}
                style={{
                  flex: 1,
                  padding: '8px 12px',
                  background: '#F6F6F0',
                  border: '1px solid rgba(71, 64, 64, 0.2)',
                  borderRadius: '6px',
                  color: '#6B6363',
                  fontSize: '11px',
                  outline: 'none',
                  fontFamily: 'var(--font-mono)',
                }}
              />
              <button
                type="button"
                onClick={handleCopyEmbed}
                style={{
                  padding: '8px 14px',
                  background: copiedEmbed ? '#489235' : '#EBEBE1',
                  border: '1px solid rgba(71, 64, 64, 0.15)',
                  borderRadius: '6px',
                  color: copiedEmbed ? '#FFFDE2' : '#474040',
                  fontWeight: 600,
                  fontSize: '12px',
                  cursor: 'pointer',
                  transition: 'background 0.15s ease',
                  whiteSpace: 'nowrap',
                }}
              >
                {copiedEmbed ? 'Copied ✓' : 'Copy'}
              </button>
            </div>
          </div>

          {/* Download Buttons */}
          <div style={{ borderTop: '1px solid rgba(71, 64, 64, 0.12)', paddingTop: '16px', display: 'flex', gap: '8px' }}>
            {meshUrl && (
              <a
                href={meshUrl}
                download={`${partName || 'part'}.stl`}
                style={{
                  flex: 1,
                  padding: '9px',
                  background: '#EBEBE1',
                  border: '1px solid rgba(71, 64, 64, 0.15)',
                  borderRadius: '6px',
                  color: '#474040',
                  fontSize: '12px',
                  fontWeight: 600,
                  textAlign: 'center',
                  textDecoration: 'none',
                }}
              >
                Download STL (.stl)
              </a>
            )}
            {stepUrl && (
              <a
                href={stepUrl}
                download={`${partName || 'part'}.step`}
                style={{
                  flex: 1,
                  padding: '9px',
                  background: '#474040',
                  border: 'none',
                  borderRadius: '6px',
                  color: '#FFFDE2',
                  fontSize: '12px',
                  fontWeight: 600,
                  textAlign: 'center',
                  textDecoration: 'none',
                }}
              >
                Download STEP (.step)
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
