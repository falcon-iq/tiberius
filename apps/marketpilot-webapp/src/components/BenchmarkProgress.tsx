import { useQuery } from '@tanstack/react-query';
import { api } from '@services/api';
import type { BenchmarkStatus } from '@app-types/api';

const CDN_BASE_URL = import.meta.env.VITE_CDN_BASE_URL as string | undefined;
const ANALYZER_BASE_URL = import.meta.env.VITE_ANALYZER_BASE_URL ?? 'http://localhost:8000';

const STEP_ORDER: BenchmarkStatus[] = [
  'NOT_STARTED',
  'CRAWL_IN_PROGRESS',
  'CRAWL_COMPLETED',
  'ANALYSIS_IN_PROGRESS',
  'ANALYSIS_COMPLETED',
  'BENCHMARK_REPORT_IN_PROGRESS',
  'COMPLETED',
];

const STEP_LABELS: Record<BenchmarkStatus, string> = {
  NOT_STARTED: 'Report created',
  CRAWL_IN_PROGRESS: 'Crawling websites',
  CRAWL_COMPLETED: 'Crawling complete',
  ANALYSIS_IN_PROGRESS: 'Analyzing websites',
  ANALYSIS_COMPLETED: 'Analysis complete',
  BENCHMARK_REPORT_IN_PROGRESS: 'Generating benchmark report',
  COMPLETED: 'Benchmark complete',
  FAILED: 'Failed',
};

const STEP_PROGRESS: Record<BenchmarkStatus, number> = {
  NOT_STARTED: 5,
  CRAWL_IN_PROGRESS: 20,
  CRAWL_COMPLETED: 40,
  ANALYSIS_IN_PROGRESS: 55,
  ANALYSIS_COMPLETED: 70,
  BENCHMARK_REPORT_IN_PROGRESS: 85,
  COMPLETED: 100,
  FAILED: 0,
};

const STATUS_MESSAGES: Record<BenchmarkStatus, string> = {
  NOT_STARTED: 'Waiting to start...',
  CRAWL_IN_PROGRESS: 'Crawling websites to gather page data...',
  CRAWL_COMPLETED: 'Crawling finished. Preparing analysis...',
  ANALYSIS_IN_PROGRESS: 'AI is analyzing each website...',
  ANALYSIS_COMPLETED: 'Analysis complete. Generating benchmark...',
  BENCHMARK_REPORT_IN_PROGRESS: 'Generating your competitive benchmark report...',
  COMPLETED: 'Your benchmark report is ready!',
  FAILED: 'Something went wrong. Please try again.',
};

interface BenchmarkProgressProps {
  jobId: string;
  onReset: () => void;
}

export function BenchmarkProgress({ jobId, onReset }: BenchmarkProgressProps) {
  const { data, error } = useQuery({
    queryKey: ['benchmark-status', jobId],
    queryFn: () => api.getBenchmarkStatus(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === 'COMPLETED' || status === 'FAILED') return false;
      return 4000;
    },
  });

  const status = data?.status ?? 'NOT_STARTED';
  const isDone = status === 'COMPLETED';
  const isFailed = status === 'FAILED';
  const isTerminal = isDone || isFailed;

  const progress = STEP_PROGRESS[status] ?? 10;
  const currentIdx = STEP_ORDER.indexOf(status);

  const reportUrl = CDN_BASE_URL
    ? `${CDN_BASE_URL}/analyzer/company-benchmarks/benchmark-${jobId}.html`
    : `${ANALYZER_BASE_URL}/company-benchmark-report/${jobId}/report`;

  return (
    <div
      style={{
        background: 'rgba(24, 24, 32, 0.8)',
        border: '1px solid rgba(63, 63, 70, 0.5)',
        borderRadius: 16,
        padding: 32,
        backdropFilter: 'blur(12px)',
      }}
    >
      {!isDone && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
          {!isTerminal && (
            <div
              style={{
                width: 20,
                height: 20,
                border: '2.5px solid rgba(99, 102, 241, 0.2)',
                borderTopColor: '#6366f1',
                borderRadius: '50%',
                animation: 'spin 0.8s linear infinite',
                flexShrink: 0,
              }}
            />
          )}
          <span
            style={{
              fontSize: 14,
              fontWeight: 600,
              color: isFailed ? '#ef4444' : '#a1a1aa',
            }}
          >
            {isDone ? 'Done!' : isFailed ? 'Failed' : 'Processing...'}
          </span>
        </div>
      )}

      {/* Progress bar */}
      <div
        style={{
          width: '100%',
          height: 6,
          background: 'rgba(63, 63, 70, 0.4)',
          borderRadius: 3,
          overflow: 'hidden',
          marginBottom: 12,
        }}
      >
        <div
          style={{
            height: '100%',
            background: isFailed ? '#ef4444' : 'linear-gradient(90deg, #6366f1, #a855f7)',
            borderRadius: 3,
            width: `${isFailed ? 0 : progress}%`,
            transition: 'width 0.6s ease',
          }}
        />
      </div>

      <div style={{ fontSize: 13, color: '#71717a', marginBottom: 20 }}>
        {error ? `Error: ${error.message}` : STATUS_MESSAGES[status]}
      </div>

      {/* Steps tracker */}
      <div>
        {STEP_ORDER.map((step, idx) => {
          const isDoneStep = idx < currentIdx || (step === 'COMPLETED' && isDone);
          const isActiveStep = idx === currentIdx && !isDone;
          const isFailedStep = isFailed && idx === currentIdx;

          const dotColor = isFailedStep
            ? '#ef4444'
            : isDoneStep
              ? '#4ade80'
              : isActiveStep
                ? '#a78bfa'
                : '#3f3f46';

          const textColor = isFailedStep
            ? '#ef4444'
            : isDoneStep
              ? '#4ade80'
              : isActiveStep
                ? '#a78bfa'
                : '#52525b';

          return (
            <div
              key={step}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '10px 0',
                borderBottom: '1px solid rgba(63, 63, 70, 0.2)',
                fontSize: 13,
                color: textColor,
                transition: 'color 0.3s',
              }}
            >
              <div
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  background: dotColor,
                  flexShrink: 0,
                  boxShadow: isActiveStep ? '0 0 8px rgba(167, 139, 250, 0.5)' : 'none',
                  animation: isActiveStep ? 'pulseDot 1.5s ease-in-out infinite' : 'none',
                  transition: 'all 0.3s',
                }}
              />
              <span>{STEP_LABELS[step]}</span>
            </div>
          );
        })}
      </div>

      {/* Completed state */}
      {isDone && (
        <div style={{ textAlign: 'center', paddingTop: 32 }}>
          <div
            style={{
              width: 64,
              height: 64,
              borderRadius: '50%',
              background: 'rgba(74, 222, 128, 0.1)',
              border: '2px solid rgba(74, 222, 128, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 20px',
              animation: 'scaleIn 0.4s ease-out',
            }}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="#4ade80" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ width: 32, height: 32 }}>
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <div style={{ fontSize: 20, fontWeight: 700, color: '#f4f4f5', marginBottom: 8 }}>
            Benchmark Complete!
          </div>
          <div style={{ fontSize: 14, color: '#71717a', marginBottom: 24 }}>
            Your competitive analysis report has been generated.
          </div>
          <a
            href={reportUrl}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'inline-block',
              padding: '14px 32px',
              border: 'none',
              borderRadius: 12,
              background: 'linear-gradient(135deg, #6366f1, #a855f7)',
              color: '#fff',
              fontSize: 15,
              fontWeight: 700,
              textDecoration: 'none',
              marginBottom: 16,
            }}
          >
            View Report
          </a>
          <br />
          <button
            onClick={onReset}
            style={{
              padding: '12px 32px',
              border: '1px solid rgba(99, 102, 241, 0.4)',
              borderRadius: 10,
              background: 'transparent',
              color: '#818cf8',
              fontSize: 14,
              fontWeight: 600,
              cursor: 'pointer',
              fontFamily: 'inherit',
            }}
          >
            Run Another Benchmark
          </button>
        </div>
      )}

      {/* Failed state */}
      {isFailed && (
        <div style={{ marginTop: 24 }}>
          <div
            style={{
              padding: '12px 16px',
              background: 'rgba(239, 68, 68, 0.08)',
              border: '1px solid rgba(239, 68, 68, 0.2)',
              borderRadius: 10,
              color: '#fca5a5',
              fontSize: 13,
              marginBottom: 16,
            }}
          >
            {data?.errorMessage ?? 'An error occurred during processing.'}
          </div>
          <button
            onClick={onReset}
            style={{
              padding: '12px 32px',
              border: '1px solid rgba(99, 102, 241, 0.4)',
              borderRadius: 10,
              background: 'transparent',
              color: '#818cf8',
              fontSize: 14,
              fontWeight: 600,
              cursor: 'pointer',
              fontFamily: 'inherit',
            }}
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}
