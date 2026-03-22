import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@services/api';
import type { BenchmarkStatus } from '@app-types/api';

const CDN_BASE_URL = import.meta.env.VITE_CDN_BASE_URL as string | undefined;
const ANALYZER_BASE_URL = import.meta.env.VITE_ANALYZER_BASE_URL ?? 'http://localhost:8000';

const STATUS_LABELS: Record<BenchmarkStatus, string> = {
  NOT_STARTED: 'Not started',
  CRAWL_IN_PROGRESS: 'Crawling websites...',
  CRAWL_COMPLETED: 'Crawling complete',
  ANALYSIS_IN_PROGRESS: 'Analyzing websites...',
  ANALYSIS_COMPLETED: 'Analysis complete',
  BENCHMARK_REPORT_IN_PROGRESS: 'Generating report...',
  COMPLETED: 'Report ready!',
  FAILED: 'Failed',
};

const cardStyle: React.CSSProperties = {
  background: 'rgba(24, 24, 32, 0.8)',
  border: '1px solid rgba(63, 63, 70, 0.5)',
  borderRadius: 16,
  padding: 24,
  backdropFilter: 'blur(12px)',
};

const inputStyle: React.CSSProperties = {
  flex: 1,
  padding: '12px 16px',
  background: 'rgba(9, 9, 11, 0.6)',
  border: '1px solid rgba(63, 63, 70, 0.6)',
  borderRadius: 10,
  color: '#f4f4f5',
  fontSize: 14,
  fontFamily: 'inherit',
  outline: 'none',
};

export function BenchmarkStatusLookup() {
  const [reportId, setReportId] = useState('');
  const [activeId, setActiveId] = useState('');

  const { data, error, isFetching } = useQuery({
    queryKey: ['benchmark-lookup', activeId],
    queryFn: () => api.getBenchmarkStatus(activeId),
    enabled: !!activeId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (!status || status === 'COMPLETED' || status === 'FAILED') return false;
      return 4000;
    },
  });

  const handleCheck = () => {
    const trimmed = reportId.trim();
    if (trimmed) setActiveId(trimmed);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleCheck();
  };

  const status = data?.status;
  const isDone = status === 'COMPLETED';
  const isFailed = status === 'FAILED';
  const isInProgress = status && !isDone && !isFailed;

  const reportUrl = activeId
    ? CDN_BASE_URL
      ? `${CDN_BASE_URL}/analyzer/company-benchmarks/benchmark-${activeId}.html`
      : `${ANALYZER_BASE_URL}/company-benchmark-report/${activeId}/report`
    : '';

  return (
    <div style={cardStyle}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
        <svg viewBox="0 0 24 24" fill="none" stroke="#71717a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: 18, height: 18, flexShrink: 0 }}>
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.3-4.3" />
        </svg>
        <div style={{ fontSize: 15, fontWeight: 600, color: '#a1a1aa' }}>Check Report Status</div>
      </div>

      <div style={{ display: 'flex', gap: 10 }}>
        <input
          type="text"
          style={inputStyle}
          placeholder="Paste your Report ID here"
          value={reportId}
          onChange={(e) => setReportId(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button
          onClick={handleCheck}
          disabled={!reportId.trim() || isFetching}
          style={{
            padding: '12px 20px',
            border: 'none',
            borderRadius: 10,
            background: !reportId.trim() ? 'rgba(63, 63, 70, 0.4)' : 'linear-gradient(135deg, #6366f1, #7c3aed)',
            color: !reportId.trim() ? '#52525b' : '#fff',
            fontSize: 14,
            fontWeight: 600,
            cursor: !reportId.trim() ? 'not-allowed' : 'pointer',
            fontFamily: 'inherit',
            flexShrink: 0,
          }}
        >
          {isFetching ? 'Checking...' : 'Check'}
        </button>
      </div>

      {/* Results */}
      {error && activeId && (
        <div style={{
          marginTop: 16,
          padding: '12px 16px',
          background: 'rgba(239, 68, 68, 0.08)',
          border: '1px solid rgba(239, 68, 68, 0.2)',
          borderRadius: 10,
          color: '#fca5a5',
          fontSize: 13,
        }}>
          Report not found. Please check the ID and try again.
        </div>
      )}

      {status && !error && (
        <div
          style={{
            marginTop: 16,
            padding: '16px',
            background: isDone
              ? 'rgba(74, 222, 128, 0.06)'
              : isFailed
                ? 'rgba(239, 68, 68, 0.06)'
                : 'rgba(99, 102, 241, 0.06)',
            border: `1px solid ${
              isDone
                ? 'rgba(74, 222, 128, 0.2)'
                : isFailed
                  ? 'rgba(239, 68, 68, 0.2)'
                  : 'rgba(99, 102, 241, 0.15)'
            }`,
            borderRadius: 10,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: isDone ? 12 : 0 }}>
            {/* Status dot */}
            <div
              style={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                background: isDone ? '#4ade80' : isFailed ? '#ef4444' : '#a78bfa',
                flexShrink: 0,
                boxShadow: isInProgress ? '0 0 8px rgba(167, 139, 250, 0.5)' : 'none',
                animation: isInProgress ? 'pulseDot 1.5s ease-in-out infinite' : 'none',
              }}
            />
            <span
              style={{
                fontSize: 14,
                fontWeight: 600,
                color: isDone ? '#4ade80' : isFailed ? '#fca5a5' : '#c4b5fd',
              }}
            >
              {STATUS_LABELS[status]}
            </span>
          </div>

          {isDone && (
            <a
              href={reportUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'inline-block',
                padding: '10px 24px',
                border: 'none',
                borderRadius: 10,
                background: 'linear-gradient(135deg, #6366f1, #a855f7)',
                color: '#fff',
                fontSize: 14,
                fontWeight: 700,
                textDecoration: 'none',
              }}
            >
              View Report
            </a>
          )}

          {isFailed && data?.errorMessage && (
            <div style={{ fontSize: 13, color: '#fca5a5', marginTop: 8 }}>
              {data.errorMessage}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
