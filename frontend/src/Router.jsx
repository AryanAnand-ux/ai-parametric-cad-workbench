import React, { lazy, Suspense, useState, useEffect } from 'react';

const App = lazy(() => import('./App.jsx'));
const LandingPage = lazy(() => import('./LandingPage.jsx'));
const Gallery = lazy(() => import('./pages/Gallery.jsx'));

function LoadingFallback() {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      background: '#F6F6F0',
      color: '#474040',
      fontFamily: 'Inter, system-ui, sans-serif',
      fontSize: '14px',
      letterSpacing: '0.08em'
    }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{
          width: '36px',
          height: '36px',
          border: '3px solid rgba(71, 64, 64, 0.15)',
          borderTop: '3px solid #474040',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
          margin: '0 auto 16px'
        }} />
        <div style={{ color: '#99908F', fontSize: '12px', letterSpacing: '0.1em' }}>LOADING…</div>
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

function getViewFromHash() {
  const hash = window.location.hash;
  if (hash === '#app') return 'app';
  if (hash === '#gallery') return 'gallery';
  return 'landing';
}

export default function Router() {
  const [view, setView] = useState(getViewFromHash);

  useEffect(() => {
    const onHash = () => setView(getViewFromHash());
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

  const goToGallery = () => {
    window.location.hash = '#gallery';
    setView('gallery');
    window.scrollTo(0, 0);
  };

  return (
    <Suspense fallback={<LoadingFallback />}>
      {view === 'app' ? (
        <App onGoHome={goToHome} onGoToGallery={goToGallery} />
      ) : view === 'gallery' ? (
        <Gallery onGoToApp={goToApp} onGoHome={goToHome} />
      ) : (
        <LandingPage onEnterApp={goToApp} onGoToGallery={goToGallery} />
      )}
    </Suspense>
  );
}

