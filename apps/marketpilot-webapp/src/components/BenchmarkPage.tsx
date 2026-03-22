import { useState, useEffect } from 'react';
import { BenchmarkForm } from './BenchmarkForm';
import { BenchmarkProgress } from './BenchmarkProgress';
import { BenchmarkStatusLookup } from './BenchmarkStatusLookup';
import { api } from '@services/api';

const STORAGE_KEY = 'falconiq_last_benchmark';

type PageState =
  | { phase: 'idle' }
  | { phase: 'submitting' }
  | { phase: 'launched'; jobId: string; email: string; companyName: string };

export function BenchmarkPage() {
  const [state, setState] = useState<PageState>(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed.jobId && parsed.phase === 'launched') return parsed;
      } catch {}
    }
    return { phase: 'idle' };
  });

  useEffect(() => {
    if (state.phase === 'launched') {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    }
  }, [state]);

  const handleSubmit = async (email: string, companyName: string, companyUrl: string, competitorUrls: string[]) => {
    setState({ phase: 'submitting' });
    try {
      const res = await api.startBenchmark({ email, companyName, companyUrl, competitorUrls });
      setState({ phase: 'launched', jobId: res.id, email, companyName });
    } catch (err) {
      setState({ phase: 'idle' });
      throw err;
    }
  };

  const handleReset = () => {
    localStorage.removeItem(STORAGE_KEY);
    setState({ phase: 'idle' });
  };

  if (state.phase === 'launched') {
    return (
      <BenchmarkLaunched
        jobId={state.jobId}
        email={state.email}
        companyName={state.companyName}
        onReset={handleReset}
      />
    );
  }

  return (
    <div>
      <BenchmarkForm
        onSubmit={handleSubmit}
        isSubmitting={state.phase === 'submitting'}
      />
      <div style={{ marginTop: 32 }}>
        <BenchmarkStatusLookup />
      </div>
    </div>
  );
}

/* ── Launched view: confirmation card + collapsible progress ── */

const cardStyle: React.CSSProperties = {
  background: 'rgba(24, 24, 32, 0.8)',
  border: '1px solid rgba(63, 63, 70, 0.5)',
  borderRadius: 16,
  padding: 32,
  backdropFilter: 'blur(12px)',
};

function BenchmarkLaunched({
  jobId,
  email,
  companyName,
  onReset,
}: {
  jobId: string;
  email: string;
  companyName: string;
  onReset: () => void;
}) {
  const [showProgress, setShowProgress] = useState(true);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(jobId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div>
      {/* Confirmation card */}
      <div style={{ ...cardStyle, marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: 12,
              background: 'linear-gradient(135deg, rgba(74, 222, 128, 0.15), rgba(16, 185, 129, 0.15))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="#4ade80" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ width: 22, height: 22 }}>
              <path d="M22 2L11 13" />
              <path d="M22 2L15 22L11 13L2 9L22 2Z" />
            </svg>
          </div>
          <div>
            <div style={{ fontSize: 20, fontWeight: 700, color: '#f4f4f5' }}>Benchmark Launched</div>
            <div style={{ fontSize: 13, color: '#71717a', marginTop: 2 }}>
              Analyzing <span style={{ color: '#a78bfa', fontWeight: 600 }}>{companyName}</span> against competitors
            </div>
          </div>
        </div>

        {/* Report ID */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '12px 16px',
            background: 'rgba(9, 9, 11, 0.6)',
            border: '1px solid rgba(63, 63, 70, 0.6)',
            borderRadius: 10,
            marginBottom: 16,
          }}
        >
          <span style={{ fontSize: 12, color: '#71717a', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', flexShrink: 0 }}>
            Report ID
          </span>
          <code style={{ fontSize: 13, color: '#e4e4e7', flex: 1, fontFamily: 'monospace', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {jobId}
          </code>
          <button
            onClick={handleCopy}
            style={{
              padding: '4px 12px',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              borderRadius: 6,
              background: copied ? 'rgba(74, 222, 128, 0.12)' : 'rgba(99, 102, 241, 0.08)',
              color: copied ? '#4ade80' : '#818cf8',
              fontSize: 12,
              fontWeight: 600,
              cursor: 'pointer',
              fontFamily: 'inherit',
              flexShrink: 0,
              transition: 'all 0.2s',
            }}
          >
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>

        {/* Email notice */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '12px 16px',
            background: 'rgba(99, 102, 241, 0.06)',
            border: '1px solid rgba(99, 102, 241, 0.15)',
            borderRadius: 10,
            marginBottom: 20,
          }}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="#818cf8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: 18, height: 18, flexShrink: 0 }}>
            <rect x="2" y="4" width="20" height="16" rx="2" />
            <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
          </svg>
          <span style={{ fontSize: 13, color: '#a1a1aa' }}>
            We'll email your report to <span style={{ color: '#c4b5fd', fontWeight: 600 }}>{email}</span> when it's ready.
          </span>
        </div>

        {/* Time estimate */}
        <div style={{ fontSize: 13, color: '#52525b', marginBottom: 20 }}>
          This typically takes 15-20 minutes. You can close this page and come back later.
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: 12 }}>
          <button
            onClick={onReset}
            style={{
              padding: '12px 24px',
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
            Launch Another Benchmark
          </button>
          <button
            onClick={() => setShowProgress(!showProgress)}
            style={{
              padding: '12px 24px',
              border: '1px solid rgba(63, 63, 70, 0.5)',
              borderRadius: 10,
              background: 'transparent',
              color: '#a1a1aa',
              fontSize: 14,
              fontWeight: 600,
              cursor: 'pointer',
              fontFamily: 'inherit',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            {showProgress ? 'Hide' : 'Show'} Progress
            <span style={{
              display: 'inline-block',
              transition: 'transform 0.2s',
              transform: showProgress ? 'rotate(180deg)' : 'rotate(0deg)',
              fontSize: 10,
            }}>
              &#9660;
            </span>
          </button>
        </div>
      </div>

      {/* Collapsible progress tracker */}
      {showProgress && (
        <div style={{ animation: 'fadeSlideIn 0.3s ease-out' }}>
          <BenchmarkProgress jobId={jobId} onReset={onReset} />
        </div>
      )}
    </div>
  );
}
