import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@services/api';
import { IndustryCard } from './IndustryCard';
import { IndustryDetailView } from './IndustryDetailView';

export function IndustryBenchmarksTab() {
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);

  const {
    data: benchmarks,
    isLoading: listLoading,
    error: listError,
    refetch: refetchList,
  } = useQuery({
    queryKey: ['industry-benchmarks'],
    queryFn: () => api.getIndustryBenchmarks(),
  });

  const {
    data: detail,
    isLoading: detailLoading,
  } = useQuery({
    queryKey: ['industry-benchmark', selectedSlug],
    queryFn: () => api.getIndustryBenchmark(selectedSlug!),
    enabled: !!selectedSlug,
  });

  if (selectedSlug && detail) {
    return (
      <div style={{ maxWidth: 900, margin: '0 auto', padding: '32px 24px' }}>
        <IndustryDetailView benchmark={detail} onBack={() => setSelectedSlug(null)} />
      </div>
    );
  }

  if (selectedSlug && detailLoading) {
    return (
      <div style={{ maxWidth: 900, margin: '0 auto', padding: '32px 24px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              style={{
                background: 'rgba(24, 24, 32, 0.8)',
                border: '1px solid rgba(63, 63, 70, 0.5)',
                borderRadius: 16,
                padding: 24,
                height: 120,
                animation: 'pulse 1.5s ease-in-out infinite',
              }}
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '32px 24px' }}>
      <div style={{ marginBottom: 32, textAlign: 'center' }}>
        <h2
          style={{
            fontSize: '2rem',
            fontWeight: 800,
            margin: '0 0 8px 0',
            background: 'linear-gradient(135deg, #3b82f6, #6366f1)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          Industry Benchmarks
        </h2>
        <p style={{ color: '#71717a', fontSize: '0.95rem', margin: 0 }}>
          Pre-computed competitive intelligence reports across industries
        </p>
      </div>

      {listLoading && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
            gap: 16,
          }}
        >
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              style={{
                background: 'rgba(24, 24, 32, 0.8)',
                border: '1px solid rgba(63, 63, 70, 0.5)',
                borderRadius: 16,
                padding: 24,
                height: 120,
                animation: 'pulse 1.5s ease-in-out infinite',
              }}
            />
          ))}
        </div>
      )}

      {listError && (
        <div
          style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 12,
            padding: 24,
            textAlign: 'center',
          }}
        >
          <p style={{ color: '#ef4444', margin: '0 0 12px 0' }}>
            Failed to load industry benchmarks
          </p>
          <button
            onClick={() => refetchList()}
            style={{
              background: 'rgba(239, 68, 68, 0.2)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: 8,
              padding: '8px 16px',
              color: '#ef4444',
              cursor: 'pointer',
              fontSize: '0.85rem',
            }}
          >
            Retry
          </button>
        </div>
      )}

      {!listLoading && !listError && benchmarks && benchmarks.length === 0 && (
        <div
          style={{
            background: 'rgba(24, 24, 32, 0.8)',
            border: '1px solid rgba(63, 63, 70, 0.5)',
            borderRadius: 16,
            padding: 48,
            textAlign: 'center',
          }}
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            stroke="#52525b"
            style={{ width: 48, height: 48, margin: '0 auto 16px' }}
          >
            <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5C7 4 9 7 12 7s5-3 7.5-3a2.5 2.5 0 0 1 0 5H18" />
            <path d="M12 7v10" />
            <path d="M8 17h8a2 2 0 1 1 0 4H8a2 2 0 1 1 0-4z" />
          </svg>
          <p style={{ color: '#71717a', fontSize: '1rem', margin: 0 }}>
            No industry benchmarks available yet
          </p>
        </div>
      )}

      {!listLoading && !listError && benchmarks && benchmarks.length > 0 && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
            gap: 16,
          }}
        >
          {benchmarks.map((b) => (
            <IndustryCard key={b.slug} benchmark={b} onClick={() => setSelectedSlug(b.slug)} />
          ))}
        </div>
      )}
    </div>
  );
}
