import React, { useState } from 'react';

export default function AuthModal({ isOpen, onClose, onLogin, onRegister }) {
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === 'login') {
        await onLogin(email, password);
      } else {
        if (!displayName.trim()) {
          throw new Error('Please provide your name');
        }
        await onRegister(email, password, displayName);
      }
      onClose();
    } catch (err) {
      setError(err.message || 'Authentication error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-card"
        style={{ maxWidth: '440px' }}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        {/* Atelier Header */}
        <div className="modal-header">
          <div className="modal-title-group">
            <span style={{ fontSize: '18px' }}>✦</span>
            <div>
              <div className="modal-title">
                {mode === 'login' ? 'Atelier Studio Sign In' : 'Join the CAD Atelier'}
              </div>
              <div className="modal-subtitle">
                {mode === 'login' ? 'Access your private workspace' : 'Create your CAD membership'}
              </div>
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
          {/* Mode Tabs */}
          <div
            style={{
              display: 'flex',
              background: '#E8E5DD',
              padding: '3px',
              borderRadius: '8px',
              marginBottom: '20px',
            }}
          >
            <button
              type="button"
              onClick={() => { setMode('login'); setError(null); }}
              style={{
                flex: 1,
                padding: '8px',
                background: mode === 'login' ? '#474040' : 'transparent',
                color: mode === 'login' ? '#FFFDE2' : '#6B6363',
                border: 'none',
                borderRadius: '6px',
                fontWeight: 600,
                fontSize: '12px',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => { setMode('register'); setError(null); }}
              style={{
                flex: 1,
                padding: '8px',
                background: mode === 'register' ? '#474040' : 'transparent',
                color: mode === 'register' ? '#FFFDE2' : '#6B6363',
                border: 'none',
                borderRadius: '6px',
                fontWeight: 600,
                fontSize: '12px',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              Register
            </button>
          </div>

          {/* Error Banner */}
          {error && (
            <div
              style={{
                padding: '10px 14px',
                background: '#FEE2E2',
                border: '1px solid #FCA5A5',
                borderRadius: '6px',
                color: '#991B1B',
                fontSize: '12px',
                marginBottom: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span>⚠️</span>
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit}>
            {mode === 'register' && (
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: '#6B6363', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="e.g. Alex Engineer"
                  style={{
                    width: '100%',
                    padding: '9px 12px',
                    background: '#FFFFFF',
                    border: '1px solid rgba(71, 64, 64, 0.2)',
                    borderRadius: '6px',
                    color: '#474040',
                    fontSize: '13px',
                    outline: 'none',
                    boxSizing: 'border-box',
                  }}
                  onFocus={(e) => (e.target.style.borderColor = '#474040')}
                  onBlur={(e) => (e.target.style.borderColor = 'rgba(71, 64, 64, 0.2)')}
                />
              </div>
            )}

            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: '#6B6363', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@organization.com"
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  background: '#FFFFFF',
                  border: '1px solid rgba(71, 64, 64, 0.2)',
                  borderRadius: '6px',
                  color: '#474040',
                  fontSize: '13px',
                  outline: 'none',
                  boxSizing: 'border-box',
                }}
                onFocus={(e) => (e.target.style.borderColor = '#474040')}
                onBlur={(e) => (e.target.style.borderColor = 'rgba(71, 64, 64, 0.2)')}
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: '#6B6363', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                minLength={6}
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  background: '#FFFFFF',
                  border: '1px solid rgba(71, 64, 64, 0.2)',
                  borderRadius: '6px',
                  color: '#474040',
                  fontSize: '13px',
                  outline: 'none',
                  boxSizing: 'border-box',
                }}
                onFocus={(e) => (e.target.style.borderColor = '#474040')}
                onBlur={(e) => (e.target.style.borderColor = 'rgba(71, 64, 64, 0.2)')}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                width: '100%',
                padding: '11px',
                background: '#474040',
                border: 'none',
                borderRadius: '6px',
                color: '#FFFDE2',
                fontWeight: 600,
                fontSize: '13px',
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.7 : 1,
                transition: 'background 0.15s ease',
              }}
              onMouseEnter={(e) => { if (!loading) e.currentTarget.style.background = '#363131'; }}
              onMouseLeave={(e) => { if (!loading) e.currentTarget.style.background = '#474040'; }}
            >
              {loading ? 'Processing...' : mode === 'login' ? 'Sign In' : 'Create Free Account'}
            </button>
          </form>

          {/* Helper hint */}
          <div
            style={{
              marginTop: '16px',
              textAlign: 'center',
              fontSize: '11px',
              color: '#99908F',
              borderTop: '1px solid rgba(71, 64, 64, 0.1)',
              paddingTop: '14px',
            }}
          >
            Demo account: <code style={{ color: '#474040', background: '#EBEBE1', padding: '2px 5px', borderRadius: '4px' }}>investor@cadstudio.ai / Password123!</code>
          </div>
        </div>
      </div>
    </div>
  );
}
