import type { Benchmark } from '@app-types/api';

interface BenchmarkHistoryProps {
  benchmarks: Benchmark[];
  onView: (jobId: string) => void;
  onDelete: (jobId: string) => void;
}

export function BenchmarkHistory({ benchmarks, onView, onDelete }: BenchmarkHistoryProps) {
  return (
    <div
      className="bg-white rounded-2xl overflow-hidden mb-5"
      style={{
        boxShadow: '0 4px 24px rgba(0,0,0,0.06), 0 1px 4px rgba(0,0,0,0.04)',
        border: '1px solid #eef0f4',
      }}
    >
      <div
        className="px-7 pt-6 pb-5"
        style={{
          borderBottom: '1px solid #f0f2f5',
          background: 'linear-gradient(135deg, #fafbff 0%, #f5f7fa 100%)',
        }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-11 h-11 rounded-xl flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #f7844a, #e74c3c)' }}
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round">
              <path d="M18 20V10M12 20V4M6 20v-6" />
            </svg>
          </div>
          <div>
            <div className="text-[18px] font-bold" style={{ color: '#1a1a2e' }}>
              Benchmark History
            </div>
            <div className="text-[13px]" style={{ color: '#9ca3af' }}>
              {benchmarks.length} completed benchmark{benchmarks.length !== 1 ? 's' : ''}
            </div>
          </div>
        </div>
      </div>

      <div className="px-7 py-5 pb-6 space-y-2">
        {benchmarks.map((b) => {
          const aW = b.company_a_wins ?? 0;
          const bW = b.company_b_wins ?? 0;
          const scoreStr = `${aW} — ${bW}`;
          const winnerLabel =
            aW > bW ? (
              <span className="font-bold text-[12px]" style={{ color: '#22c55e' }}>
                🏆 {b.company_a} wins
              </span>
            ) : bW > aW ? (
              <span className="font-bold text-[12px]" style={{ color: '#22c55e' }}>
                🏆 {b.company_b} wins
              </span>
            ) : (
              <span className="font-semibold text-[12px]" style={{ color: '#9ca3af' }}>
                Tie
              </span>
            );
          const dateStr = b.created_at
            ? new Date(b.created_at).toLocaleDateString(undefined, {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
              })
            : '';

          return (
            <div
              key={b.job_id}
              className="flex items-center gap-4 px-4 py-3.5 rounded-xl cursor-pointer transition-all"
              style={{ background: '#f8f9fc', border: '1px solid #eef0f4' }}
              onClick={() => onView(b.job_id)}
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
                style={{ background: 'linear-gradient(135deg,#fde6d8,#fdd0b5)', color: '#e74c3c' }}
              >
                ⚖
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[14px] font-semibold" style={{ color: '#1a1a2e' }}>
                  {b.company_a} vs {b.company_b}
                </div>
                <div className="flex gap-4 mt-1 text-[12px] flex-wrap" style={{ color: '#9ca3af' }}>
                  <span className="font-bold" style={{ color: '#1a1a2e' }}>
                    {scoreStr}
                  </span>
                  {winnerLabel}
                  <span>{b.total_prompts} prompts</span>
                  {dateStr && <span>{dateStr}</span>}
                  <span className="text-[11px]" style={{ color: '#ccc' }}>
                    {b.job_id}
                  </span>
                </div>
              </div>
              <div className="flex gap-2 flex-shrink-0">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onView(b.job_id);
                  }}
                  className="px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-colors"
                  style={{ background: '#f0f4ff', color: '#4a6cf7', border: '1px solid #d0d7f7' }}
                >
                  View
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(b.job_id);
                  }}
                  className="p-1.5 rounded-lg transition-colors hover:bg-red-50"
                  style={{ color: '#dc3545' }}
                  title="Delete benchmark"
                >
                  <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                    <polyline points="3 6 5 6 21 6" />
                    <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
                  </svg>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
