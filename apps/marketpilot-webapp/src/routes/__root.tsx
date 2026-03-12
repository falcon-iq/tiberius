import { createRootRoute, Outlet } from '@tanstack/react-router';

export const Route = createRootRoute({
  component: RootLayout,
});

function RootLayout() {
  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#0a0a0f', overflowX: 'hidden' }}>
      {/* Animated gradient background */}
      <div
        style={{
          position: 'fixed',
          top: '-50%',
          left: '-50%',
          width: '200%',
          height: '200%',
          background:
            'radial-gradient(ellipse at 30% 20%, rgba(99, 102, 241, 0.08) 0%, transparent 50%),' +
            'radial-gradient(ellipse at 70% 80%, rgba(168, 85, 247, 0.06) 0%, transparent 50%),' +
            'radial-gradient(ellipse at 50% 50%, rgba(59, 130, 246, 0.04) 0%, transparent 70%)',
          animation: 'bgShift 20s ease-in-out infinite alternate',
          pointerEvents: 'none',
          zIndex: 0,
        }}
      />
      <div style={{ position: 'relative', zIndex: 1, maxWidth: 720, margin: '0 auto', padding: '48px 24px 80px' }}>
        <div style={{ textAlign: 'center', marginBottom: 48 }}>
          <div
            style={{
              width: 56,
              height: 56,
              margin: '0 auto 20px',
              background: 'linear-gradient(135deg, #6366f1, #a855f7)',
              borderRadius: 16,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 40px rgba(99, 102, 241, 0.3)',
            }}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: 28, height: 28 }}>
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>
          <h1
            style={{
              fontSize: 36,
              fontWeight: 800,
              letterSpacing: '-0.03em',
              background: 'linear-gradient(135deg, #e0e7ff, #c4b5fd, #a78bfa)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              marginBottom: 8,
            }}
          >
            Market Pilot
          </h1>
          <p style={{ fontSize: 15, color: '#71717a', fontWeight: 400 }}>
            See how AI perceives your brand vs. the competition
          </p>
        </div>
        <Outlet />
      </div>
    </div>
  );
}
