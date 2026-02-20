import { createRootRoute, Outlet } from '@tanstack/react-router';
import { TopNav } from '@components/nav/TopNav';

export const Route = createRootRoute({
  component: RootLayout,
});

function RootLayout() {
  return (
    <div className="min-h-screen" style={{ backgroundColor: '#f5f7fa' }}>
      <div className="max-w-[960px] mx-auto px-5 py-5">
        <div className="text-center mb-2">
          <h1
            className="text-[28px] font-bold tracking-tight"
            style={{
              background: 'linear-gradient(135deg, #4a6cf7, #7c3aed)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
          >
            Falcon IQ Analyzer
          </h1>
        </div>
        <p className="text-center text-[14px] mb-6" style={{ color: '#666' }}>
          Crawl websites, analyze offerings, and benchmark competitive positioning
        </p>
        <TopNav />
        <Outlet />
      </div>
    </div>
  );
}
