import { useState } from 'react';
import type { Analysis } from '@app-types/api';
import { ProgressBar } from '@components/shared/ProgressBar';

interface NewBenchmarkFormProps {
  analyses: Analysis[];
  isRunning: boolean;
  benchmarkPct: number;
  benchmarkMessage: string | null;
  benchmarkError: string | null;
  onStartBenchmark: (jobIdA: string, jobIdB: string, numPrompts: number) => void;
}

export function NewBenchmarkForm({
  analyses,
  isRunning,
  benchmarkPct,
  benchmarkMessage,
  benchmarkError,
  onStartBenchmark,
}: NewBenchmarkFormProps) {
  const [jobIdA, setJobIdA] = useState('');
  const [jobIdB, setJobIdB] = useState('');
  const [numPrompts, setNumPrompts] = useState(15);

  const handleStart = () => {
    if (!jobIdA || !jobIdB) {
      alert('Please select both analyses');
      return;
    }
    if (jobIdA === jobIdB) {
      alert('Please select two different analyses');
      return;
    }
    onStartBenchmark(jobIdA, jobIdB, numPrompts);
  };

  return (
    <div
      className="rounded-xl p-6 mb-5"
      style={{
        border: '2px dashed #d0d7f7',
        background: 'linear-gradient(135deg, #fafbff 0%, #f0f4ff 100%)',
      }}
    >
      <div className="flex items-center gap-3 mb-4">
        <div
          className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
          style={{ background: 'linear-gradient(135deg, #4a6cf7, #7c3aed)' }}
        >
          <svg className="w-4.5 h-4.5" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round">
            <path d="M18 20V10M12 20V4M6 20v-6" />
          </svg>
        </div>
        <div>
          <div className="text-[16px] font-bold" style={{ color: '#1a1a2e' }}>
            New Benchmark
          </div>
          <div className="text-[13px]" style={{ color: '#9ca3af' }}>
            Compare how LLMs perceive two companies
          </div>
        </div>
      </div>

      <div className="flex gap-3 items-end flex-wrap mb-3">
        <div className="flex-1 min-w-[160px]">
          <label className="block text-[13px] font-semibold mb-1" style={{ color: '#555' }}>
            Company A
          </label>
          <select
            value={jobIdA}
            onChange={(e) => setJobIdA(e.target.value)}
            disabled={isRunning}
            className="w-full px-3 py-2.5 rounded-lg text-[14px] focus:outline-none disabled:opacity-60"
            style={{ border: '1px solid #d0d7f7' }}
          >
            <option value="">-- Select analysis --</option>
            {analyses.map((a) => (
              <option key={a.job_id} value={a.job_id}>
                {a.company_name} ({a.job_id})
              </option>
            ))}
          </select>
        </div>
        <div className="flex-1 min-w-[160px]">
          <label className="block text-[13px] font-semibold mb-1" style={{ color: '#555' }}>
            Company B
          </label>
          <select
            value={jobIdB}
            onChange={(e) => setJobIdB(e.target.value)}
            disabled={isRunning}
            className="w-full px-3 py-2.5 rounded-lg text-[14px] focus:outline-none disabled:opacity-60"
            style={{ border: '1px solid #d0d7f7' }}
          >
            <option value="">-- Select analysis --</option>
            {analyses.map((a) => (
              <option key={a.job_id} value={a.job_id}>
                {a.company_name} ({a.job_id})
              </option>
            ))}
          </select>
        </div>
        <div className="w-28">
          <label className="block text-[13px] font-semibold mb-1" style={{ color: '#555' }}>
            Prompts
          </label>
          <input
            type="number"
            value={numPrompts}
            onChange={(e) => setNumPrompts(parseInt(e.target.value) || 15)}
            min={1}
            max={50}
            disabled={isRunning}
            className="w-full px-3 py-2.5 rounded-lg text-[14px] focus:outline-none disabled:opacity-60"
            style={{ border: '1px solid #d0d7f7' }}
          />
        </div>
      </div>

      <button
        onClick={handleStart}
        disabled={isRunning}
        className="w-full py-2.5 text-white rounded-xl text-[14px] font-semibold transition-colors disabled:cursor-not-allowed"
        style={{ background: isRunning ? '#b0b8d1' : '#4a6cf7' }}
        onMouseEnter={(e) => {
          if (!isRunning) (e.currentTarget as HTMLElement).style.background = '#3a5ce5';
        }}
        onMouseLeave={(e) => {
          if (!isRunning) (e.currentTarget as HTMLElement).style.background = '#4a6cf7';
        }}
      >
        {isRunning ? (
          <span className="flex items-center justify-center gap-2">
            <span className="spinner-icon" /> Running...
          </span>
        ) : (
          '▶ Run Benchmark'
        )}
      </button>

      {isRunning && benchmarkMessage && (
        <div className="mt-4">
          <ProgressBar pct={benchmarkPct} message={benchmarkMessage} />
        </div>
      )}

      {benchmarkError && (
        <p className="text-[13px] mt-2" style={{ color: '#dc3545' }}>
          {benchmarkError}
        </p>
      )}
    </div>
  );
}
