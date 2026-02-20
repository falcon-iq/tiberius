import { useState } from 'react';
import type { LocalSite } from '@app-types/api';
import { ProgressBar } from '@components/shared/ProgressBar';
import { MarkdownRenderer } from '@components/shared/MarkdownRenderer';

interface AnalyzeSectionProps {
  site: LocalSite;
  analyzePct: number;
  analyzeMessage: string;
  analyzeError: string | null;
  latestAnalysisReport: string | null;
  onStartAnalyze: (companyName: string) => void;
}

export function AnalyzeSection({
  site,
  analyzePct,
  analyzeMessage,
  analyzeError,
  latestAnalysisReport,
  onStartAnalyze,
}: AnalyzeSectionProps) {
  const defaultName = site.domain.replace(/^www\./, '').split('.')[0] ?? site.domain;
  const [companyName, setCompanyName] = useState(defaultName);

  if (site.status === 'analyzing') {
    return (
      <div className="py-2 mt-3" style={{ borderTop: '1px solid #f0f2f5' }}>
        <div
          className="text-[11px] font-bold uppercase tracking-widest mb-1.5"
          style={{ color: '#9ca3af' }}
        >
          Analysis in progress
        </div>
        <ProgressBar pct={analyzePct} message={analyzeMessage} />
      </div>
    );
  }

  const handleAnalyze = () => {
    if (!companyName.trim()) {
      alert('Please enter a company name');
      return;
    }
    onStartAnalyze(companyName.trim());
  };

  return (
    <div className="py-3.5 mt-3" style={{ borderTop: '1px solid #f0f2f5' }}>
      <div
        className="text-[11px] font-bold uppercase tracking-widest mb-1.5"
        style={{ color: '#9ca3af' }}
      >
        Analyze
      </div>
      <div className="flex gap-2.5 items-end flex-wrap">
        <input
          type="text"
          value={companyName}
          onChange={(e) => setCompanyName(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
          placeholder="Company name"
          className="flex-1 min-w-[180px] px-3 py-2 rounded-lg text-[13px] focus:outline-none"
          style={{ border: '1px solid #ddd' }}
        />
        <button
          onClick={handleAnalyze}
          className="px-3.5 py-2 text-white rounded-lg text-[12px] font-semibold transition-colors"
          style={{ background: '#28a745' }}
          onMouseEnter={(e) =>
            (e.currentTarget.style.background = '#218838')
          }
          onMouseLeave={(e) =>
            (e.currentTarget.style.background = '#28a745')
          }
        >
          ▶ Analyze
        </button>
      </div>
      {analyzeError && (
        <p className="text-[13px] mt-2" style={{ color: '#dc3545' }}>
          {analyzeError}
        </p>
      )}
      {latestAnalysisReport && (
        <details
          className="mt-3 p-3 rounded-xl"
          style={{ background: '#f0f4ff', border: '1px solid #d0d7f7' }}
        >
          <summary
            className="cursor-pointer text-[13px] font-semibold list-none flex items-center gap-1.5"
            style={{ color: '#4a6cf7' }}
          >
            <svg
              className="w-4 h-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#4a6cf7"
              strokeWidth="2.5"
              strokeLinecap="round"
            >
              <path d="M9 18l6-6-6-6" />
            </svg>
            View Latest Analysis Report
          </summary>
          <div className="mt-3 pt-3" style={{ borderTop: '1px solid #d0d7f7' }}>
            <MarkdownRenderer content={latestAnalysisReport} />
          </div>
        </details>
      )}
    </div>
  );
}
