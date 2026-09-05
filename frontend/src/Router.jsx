import React, { lazy, Suspense, useState, useEffect } from 'react';

const App = lazy(() => import('./App.jsx'));
const LandingPage = lazy(() => import('./LandingPage.jsx'));

function LoadingFallback() {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      background: '#090d16',
      color: '#00f0ff',
      fontFamily: 'Inter, system-ui, sans-serif',
      fontSize: '14px',
      letterSpacing: '0.08em'
    }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{
          width: '36px',
          height: '36px',
          border: '3px solid rgba(0, 240, 255, 0.2)',
          borderTop: '3px solid #00f0ff',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
          margin: '0 auto 16px'
        }} />
        <div>LOADING WORKBENCH...</div>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    </div>
  );
}

export default function Router() {
  const [view, setView] = useState(() =>
    window.location.hash === '#app' ? 'app' : 'landing'
  );

  useEffect(() => {
    const onHash = () => setView(window.location.hash === '#app' ? 'app' : 'landing');
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  const goToApp = () => {
    window.location.hash = '#app';
    setView('app');
    window.scrollTo(0, 0);
  };

  const goToHome = () => {
    window.location.hash = '';
    setView('landing');
  };

  return (
    <Suspense fallback={<LoadingFallback />}>
      {view === 'app' ? (
        <App onGoHome={goToHome} />
      ) : (
        <LandingPage onEnterApp={goToApp} />
      )}
    </Suspense>
  );
}
