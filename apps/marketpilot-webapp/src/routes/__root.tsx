import { createRootRoute, Outlet } from '@tanstack/react-router';

export const Route = createRootRoute({
  component: RootLayout,
});

function RootLayout() {
  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#06060b', overflowX: 'hidden' }}>
      {/* Layered animated background */}

      {/* Layer 1: Deep mesh gradient */}
      <div
        style={{
          position: 'fixed',
          inset: 0,
          background:
            'radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99, 102, 241, 0.12) 0%, transparent 60%),' +
            'radial-gradient(ellipse 60% 40% at 100% 50%, rgba(139, 92, 246, 0.08) 0%, transparent 50%),' +
            'radial-gradient(ellipse 60% 40% at 0% 80%, rgba(59, 130, 246, 0.06) 0%, transparent 50%)',
          pointerEvents: 'none',
          zIndex: 0,
        }}
      />

      {/* Layer 2: Floating orbs */}
      <div
        style={{
          position: 'fixed',
          top: '-30%',
          left: '-20%',
          width: '160%',
          height: '160%',
          background:
            'radial-gradient(circle 600px at 20% 30%, rgba(99, 102, 241, 0.07) 0%, transparent 70%),' +
            'radial-gradient(circle 500px at 80% 70%, rgba(168, 85, 247, 0.06) 0%, transparent 70%),' +
            'radial-gradient(circle 400px at 60% 20%, rgba(236, 72, 153, 0.04) 0%, transparent 70%),' +
            'radial-gradient(circle 300px at 30% 80%, rgba(59, 130, 246, 0.05) 0%, transparent 70%)',
          animation: 'floatOrbs 25s ease-in-out infinite alternate',
          pointerEvents: 'none',
          zIndex: 0,
        }}
      />

      {/* Layer 3: Subtle grid overlay */}
      <div
        style={{
          position: 'fixed',
          inset: 0,
          backgroundImage:
            'linear-gradient(rgba(99, 102, 241, 0.03) 1px, transparent 1px),' +
            'linear-gradient(90deg, rgba(99, 102, 241, 0.03) 1px, transparent 1px)',
          backgroundSize: '64px 64px',
          maskImage: 'radial-gradient(ellipse 60% 50% at 50% 30%, black 0%, transparent 70%)',
          WebkitMaskImage: 'radial-gradient(ellipse 60% 50% at 50% 30%, black 0%, transparent 70%)',
          pointerEvents: 'none',
          zIndex: 0,
        }}
      />

      {/* Layer 4: Animated aurora streaks */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: '10%',
          right: '10%',
          height: '50%',
          background:
            'linear-gradient(180deg, transparent 0%, rgba(99, 102, 241, 0.02) 30%, rgba(168, 85, 247, 0.03) 50%, transparent 100%)',
          filter: 'blur(60px)',
          animation: 'auroraShift 15s ease-in-out infinite alternate',
          pointerEvents: 'none',
          zIndex: 0,
        }}
      />

      {/* Layer 5: Noise texture overlay */}
      <div
        style={{
          position: 'fixed',
          inset: 0,
          opacity: 0.03,
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
          pointerEvents: 'none',
          zIndex: 0,
        }}
      />

      {/* Content */}
      <div style={{ position: 'relative', zIndex: 1, maxWidth: 760, margin: '0 auto', padding: '40px 24px 80px' }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <div
            style={{
              width: 60,
              height: 60,
              margin: '0 auto 20px',
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6, #a855f7)',
              borderRadius: 18,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 50px rgba(99, 102, 241, 0.35), 0 0 100px rgba(139, 92, 246, 0.15)',
              position: 'relative',
            }}
          >
            {/* Glow ring */}
            <div
              style={{
                position: 'absolute',
                inset: -3,
                borderRadius: 21,
                background: 'linear-gradient(135deg, rgba(99,102,241,0.4), rgba(168,85,247,0.4))',
                filter: 'blur(8px)',
                zIndex: -1,
              }}
            />
            <svg viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: 30, height: 30 }}>
              <circle cx="11" cy="11" r="8" />
              <path d="M21 21l-4.35-4.35" />
            </svg>
          </div>
          <h1
            style={{
              fontSize: 42,
              fontWeight: 700,
              letterSpacing: '-0.04em',
              background: 'linear-gradient(135deg, #f0f0ff 0%, #e0e7ff 30%, #c4b5fd 60%, #a78bfa 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              marginBottom: 10,
              fontFamily: "'Inter', sans-serif",
            }}
          >
            Market Presence
          </h1>
          <p style={{ fontSize: 16, color: '#71717a', fontWeight: 400, letterSpacing: '0.01em' }}>
            The closed-loop LLM marketing engine for the AI era
          </p>
        </div>
        <Outlet />
      </div>
    </div>
  );
}
