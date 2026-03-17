import type { IndustryBenchmarkSummary } from '@app-types/api';

interface Props {
  benchmark: IndustryBenchmarkSummary;
  onClick: () => void;
}

export function IndustryCard({ benchmark, onClick }: Props) {
  return (
    <div
      onClick={onClick}
      style={{
        background: 'rgba(24, 24, 32, 0.8)',
        border: '1px solid rgba(63, 63, 70, 0.5)',
        borderRadius: 16,
        padding: 24,
        backdropFilter: 'blur(12px)',
        cursor: 'pointer',
        transition: 'all 0.25s ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = 'rgba(99, 102, 241, 0.5)';
        e.currentTarget.style.transform = 'translateY(-2px)';
        e.currentTarget.style.boxShadow = '0 8px 30px rgba(99, 102, 241, 0.1)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'rgba(63, 63, 70, 0.5)';
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = 'none';
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: 12,
                background: 'linear-gradient(135deg, #3b82f6, #6366f1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                stroke="#fff"
                style={{ width: 20, height: 20 }}
              >
                <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5C7 4 9 7 12 7s5-3 7.5-3a2.5 2.5 0 0 1 0 5H18" />
                <path d="M12 7v10" />
                <path d="M8 17h8a2 2 0 1 1 0 4H8a2 2 0 1 1 0-4z" />
              </svg>
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600, color: '#f4f4f5' }}>
                {benchmark.industryName}
              </h3>
              <span style={{ fontSize: '0.8rem', color: '#71717a' }}>{benchmark.country}</span>
            </div>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              marginTop: 8,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <svg
                viewBox="0 0 24 24"
                fill="none"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                stroke="#71717a"
                style={{ width: 14, height: 14 }}
              >
                <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                <circle cx="8.5" cy="7" r="4" />
                <path d="M20 8v6M23 11h-6" />
              </svg>
              <span style={{ fontSize: '0.8rem', color: '#a1a1aa' }}>
                {benchmark.companyCount} companies
              </span>
            </div>
            {benchmark.generatedAt && (
              <span style={{ fontSize: '0.75rem', color: '#52525b' }}>
                {new Date(benchmark.generatedAt).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                })}
              </span>
            )}
          </div>
        </div>

        <svg
          viewBox="0 0 24 24"
          fill="none"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          stroke="#52525b"
          style={{ width: 20, height: 20, marginTop: 4 }}
        >
          <path d="M9 18l6-6-6-6" />
        </svg>
      </div>
    </div>
  );
}
