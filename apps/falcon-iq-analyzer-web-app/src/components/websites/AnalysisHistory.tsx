import type { Analysis } from '@app-types/api';

interface AnalysisHistoryProps {
  analyses: Analysis[];
  onDeleteAnalysis: (jobId: string) => void;
}

export function AnalysisHistory({ analyses, onDeleteAnalysis }: AnalysisHistoryProps) {
  if (analyses.length === 0) return null;

  return (
    <div className="mt-1 pt-4" style={{ borderTop: '1px solid #f0f2f5' }}>
      <div
        className="text-[12px] font-bold uppercase tracking-widest mb-3 flex items-center gap-2"
        style={{ color: '#9ca3af' }}
      >
        Analysis History
        <span
          className="text-[11px] px-2 py-0.5 rounded-full font-bold"
          style={{ background: '#e9ecef', color: '#6c757d' }}
        >
          {analyses.length}
        </span>
      </div>
      <div className="space-y-2">
        {analyses.map((a) => {
          const dateStr = a.created_at
            ? new Date(a.created_at).toLocaleDateString(undefined, {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
              })
            : '—';
          const timeStr = a.created_at
            ? new Date(a.created_at).toLocaleTimeString(undefined, {
                hour: '2-digit',
                minute: '2-digit',
              })
            : '';

          return (
            <div
              key={a.job_id}
              className="flex items-center gap-4 px-4 py-3.5 rounded-xl transition-all"
              style={{
                background: '#f8f9fc',
                border: '1px solid #eef0f4',
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLElement).style.background = '#f0f4ff';
                (e.currentTarget as HTMLElement).style.borderColor = '#d0d7f7';
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLElement).style.background = '#f8f9fc';
                (e.currentTarget as HTMLElement).style.borderColor = '#eef0f4';
              }}
            >
              <div
                className="w-9 h-9 rounded-xl flex items-center justify-center text-base flex-shrink-0"
                style={{
                  background: 'linear-gradient(135deg, #d2f4ea, #a7f3d0)',
                  color: '#0d6e5e',
                }}
              >
                📊
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[14px] font-semibold" style={{ color: '#1a1a2e' }}>
                  {a.company_name}
                </div>
                <div
                  className="flex gap-4 mt-1 text-[12px] flex-wrap"
                  style={{ color: '#9ca3af' }}
                >
                  <span className="flex items-center gap-1">
                    <svg
                      className="w-3 h-3"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <rect x="3" y="4" width="18" height="18" rx="2" />
                      <line x1="16" y1="2" x2="16" y2="6" />
                      <line x1="8" y1="2" x2="8" y2="6" />
                      <line x1="3" y1="10" x2="21" y2="10" />
                    </svg>
                    {dateStr} {timeStr}
                  </span>
                  <span>{a.total_pages ?? '—'} pages</span>
                  <span>{a.product_pages_analyzed ?? '—'} products</span>
                  <span className="text-[11px]" style={{ color: '#ccc' }}>
                    {a.job_id}
                  </span>
                </div>
              </div>
              <button
                onClick={() => onDeleteAnalysis(a.job_id)}
                className="p-1.5 rounded-lg flex-shrink-0 transition-colors hover:bg-red-50"
                style={{ color: '#dc3545' }}
                title="Delete analysis"
              >
                <svg
                  className="w-3.5 h-3.5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                >
                  <polyline points="3 6 5 6 21 6" />
                  <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
                </svg>
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
