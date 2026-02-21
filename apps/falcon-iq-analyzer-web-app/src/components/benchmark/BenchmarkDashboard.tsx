import { useState } from 'react';
import type {
  BenchmarkResult,
  BenchmarkSummary,
  BenchmarkEvaluation,
  CompanyMention,
} from '@app-types/api';

interface BenchmarkDashboardProps {
  result: BenchmarkResult;
}

function sentimentColor(v: number): string {
  if (v >= 0.5) return '#22c55e';
  if (v >= 0.2) return '#84cc16';
  if (v >= -0.2) return '#eab308';
  if (v >= -0.5) return '#f97316';
  return '#ef4444';
}

function PillList({ items, variant }: { items?: string[]; variant: 'green' | 'red' }) {
  if (!items || items.length === 0) {
    return <span className="text-[12px]" style={{ color: '#aaa' }}>None noted</span>;
  }
  const styles =
    variant === 'green'
      ? { background: '#d4edda', color: '#155724' }
      : { background: '#f8d7da', color: '#721c24' };
  return (
    <div className="flex flex-wrap gap-1">
      {items.map((item, i) => (
        <span key={i} className="inline-block px-3 py-1 rounded-full text-[12px] font-semibold" style={styles}>
          {item}
        </span>
      ))}
    </div>
  );
}

function HeroBanner({ summary }: { summary: BenchmarkSummary }) {
  const { company_a: cA, company_b: cB, company_a_wins: aWins, company_b_wins: bWins } = summary;
  const winner = aWins > bWins ? cA : bWins > aWins ? cB : null;

  return (
    <div
      className="rounded-xl p-8 text-center text-white mb-6"
      style={{
        background: 'linear-gradient(135deg, #4a6cf7, #7c3aed)',
        animation: 'slideIn 0.6s ease-out',
      }}
    >
      <div className="text-[14px] opacity-85 uppercase tracking-[2px] mb-2">
        {cA} vs {cB}
      </div>
      <div className="text-[48px] font-black my-3 tracking-[4px]">
        {aWins} &mdash; {bWins}
      </div>
      <div className="text-[20px] font-bold">
        {winner ? (
          <>
            <span className="text-[28px]">🏆</span> {winner} WINS
          </>
        ) : (
          "It's a Tie!"
        )}
      </div>
    </div>
  );
}

function MetricCards({ summary }: { summary: BenchmarkSummary }) {
  const { total_prompts, company_a, company_b, company_a_wins: aWins, company_b_wins: bWins, ties } = summary;
  const aPct = Math.round((aWins / (total_prompts || 1)) * 100);
  const bPct = Math.round((bWins / (total_prompts || 1)) * 100);

  return (
    <div className="grid grid-cols-4 gap-4 mb-6">
      {[
        { label: 'Total Prompts', value: total_prompts, color: '#1a1a2e', pct: null },
        { label: `${company_a} Wins`, value: aWins, color: '#4a6cf7', pct: aPct },
        { label: `${company_b} Wins`, value: bWins, color: '#f7844a', pct: bPct },
        { label: 'Ties', value: ties, color: '#adb5bd', pct: null },
      ].map((m) => (
        <div key={m.label} className="bg-white rounded-xl p-5 text-center shadow-[0_2px_8px_rgba(0,0,0,0.06)]">
          <div className="text-[12px] uppercase tracking-wide mb-2" style={{ color: '#888' }}>
            {m.label}
          </div>
          <div className="text-[32px] font-black" style={{ color: m.color }}>
            {m.value}
          </div>
          {m.pct !== null && (
            <div className="bg-[#e9ecef] rounded h-1.5 mt-2.5 overflow-hidden">
              <div
                className="h-full rounded"
                style={{ width: `${m.pct}%`, background: m.color, animation: 'growWidth 1s ease-out forwards' }}
              />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function WinRateBar({ summary }: { summary: BenchmarkSummary }) {
  const { total_prompts, company_a, company_b, company_a_wins: aWins, company_b_wins: bWins } = summary;
  const total = total_prompts || 1;
  const aPct = Math.round((aWins / total) * 100);
  const bPct = Math.round((bWins / total) * 100);
  const tPct = 100 - aPct - bPct;

  return (
    <div className="bg-white rounded-xl p-6 shadow-[0_2px_8px_rgba(0,0,0,0.06)] mb-6">
      <h3 className="text-[14px] font-semibold mb-2" style={{ color: '#555' }}>
        Win Rate Distribution
      </h3>
      <div className="flex h-9 rounded-lg overflow-hidden text-[12px] font-bold text-white">
        {aPct > 0 && (
          <div className="flex items-center justify-center" style={{ width: `${aPct}%`, background: '#4a6cf7' }}>
            {aPct}%
          </div>
        )}
        {tPct > 0 && (
          <div className="flex items-center justify-center" style={{ width: `${tPct}%`, background: '#adb5bd' }}>
            {tPct}%
          </div>
        )}
        {bPct > 0 && (
          <div className="flex items-center justify-center" style={{ width: `${bPct}%`, background: '#f7844a' }}>
            {bPct}%
          </div>
        )}
      </div>
      <div className="flex gap-5 mt-2 text-[12px]" style={{ color: '#666' }}>
        {[
          { label: company_a, color: '#4a6cf7' },
          { label: 'Tie', color: '#adb5bd' },
          { label: company_b, color: '#f7844a' },
        ].map((l) => (
          <span key={l.label} className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm inline-block" style={{ background: l.color }} />
            {l.label}
          </span>
        ))}
      </div>
    </div>
  );
}

function SentimentGauges({ summary }: { summary: BenchmarkSummary }) {
  const { company_a, company_b, company_a_avg_sentiment: aS, company_b_avg_sentiment: bS } = summary;

  const Gauge = ({ company, value }: { company: string; value: number }) => {
    const pct = ((value + 1) / 2) * 100;
    const col = sentimentColor(value);
    return (
      <div className="bg-white rounded-xl p-5 shadow-[0_2px_8px_rgba(0,0,0,0.06)]">
        <div className="text-[12px] uppercase tracking-wide mb-1" style={{ color: '#888' }}>
          Avg Sentiment
        </div>
        <div className="text-[16px] font-bold mb-3" style={{ color: '#1a1a2e' }}>
          {company}
        </div>
        <div className="text-[28px] font-black mb-2.5" style={{ color: col }}>
          {value.toFixed(2)}
        </div>
        <div className="relative bg-[#e9ecef] rounded h-2.5">
          <div
            className="absolute top-0 h-full rounded opacity-30"
            style={{
              width: `${pct}%`,
              background: 'linear-gradient(90deg,#ef4444,#eab308,#22c55e)',
              transition: 'width 1s ease-out',
            }}
          />
          <div
            className="absolute top-[-3px] w-1 h-4 rounded-sm"
            style={{
              left: `${pct}%`,
              background: '#1a1a2e',
              transform: 'translateX(-50%)',
              transition: 'left 1s ease-out',
            }}
          />
        </div>
        <div className="flex justify-between text-[11px] mt-1" style={{ color: '#aaa' }}>
          <span>-1.0</span>
          <span>0</span>
          <span>+1.0</span>
        </div>
      </div>
    );
  };

  return (
    <div className="grid grid-cols-2 gap-4 mb-6">
      <Gauge company={company_a} value={aS} />
      <Gauge company={company_b} value={bS} />
    </div>
  );
}

function CategoryBreakdown({
  summary,
  evaluations,
}: {
  summary: BenchmarkSummary;
  evaluations: BenchmarkEvaluation[];
}) {
  const { company_a: cA, company_b: cB } = summary;
  const categories: Record<string, { a: number; b: number; total: number }> = {};

  evaluations.forEach((ev) => {
    const cat = ev.category ?? 'other';
    if (!categories[cat]) categories[cat] = { a: 0, b: 0, total: 0 };
    categories[cat].total++;
    if (ev.winner === 'company_a') categories[cat].a++;
    else if (ev.winner === 'company_b') categories[cat].b++;
  });

  return (
    <div className="bg-white rounded-xl p-6 shadow-[0_2px_8px_rgba(0,0,0,0.06)] mb-6">
      <h3 className="text-[14px] font-semibold mb-2" style={{ color: '#555' }}>
        Category Breakdown
      </h3>
      <table className="w-full border-separate border-spacing-0">
        <thead>
          <tr>
            {['Category', 'Prompts', cA, cB, 'Distribution'].map((h) => (
              <th
                key={h}
                className="text-left text-[12px] uppercase tracking-wide px-3 py-2"
                style={{ color: '#888', borderBottom: '2px solid #e9ecef' }}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Object.entries(categories).map(([cat, counts]) => {
            const catTotal = counts.total || 1;
            const aW = Math.round((counts.a / catTotal) * 100);
            const bW = Math.round((counts.b / catTotal) * 100);
            return (
              <tr key={cat}>
                <td className="px-3 py-2.5 text-[14px] font-semibold capitalize" style={{ borderBottom: '1px solid #f0f0f0', color: '#333' }}>
                  {cat.replace(/_/g, ' ')}
                </td>
                <td className="px-3 py-2.5 text-[14px]" style={{ borderBottom: '1px solid #f0f0f0' }}>
                  {counts.total}
                </td>
                <td className="px-3 py-2.5 text-[14px]" style={{ borderBottom: '1px solid #f0f0f0' }}>
                  {counts.a}
                </td>
                <td className="px-3 py-2.5 text-[14px]" style={{ borderBottom: '1px solid #f0f0f0' }}>
                  {counts.b}
                </td>
                <td className="px-3 py-2.5" style={{ borderBottom: '1px solid #f0f0f0' }}>
                  <div className="flex h-2 rounded overflow-hidden min-w-[120px]">
                    <div style={{ width: `${aW}%`, background: '#4a6cf7' }} />
                    <div style={{ width: `${bW}%`, background: '#f7844a' }} />
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function PerceptionPanels({ summary }: { summary: BenchmarkSummary }) {
  const {
    company_a: cA,
    company_b: cB,
    company_a_top_strengths: aStr,
    company_a_top_weaknesses: aWeak,
    company_b_top_strengths: bStr,
    company_b_top_weaknesses: bWeak,
  } = summary;

  return (
    <div className="grid grid-cols-2 gap-4 mb-6">
      {[
        { company: cA, color: '#4a6cf7', strengths: aStr, weaknesses: aWeak },
        { company: cB, color: '#f7844a', strengths: bStr, weaknesses: bWeak },
      ].map((p) => (
        <div
          key={p.company}
          className="bg-white rounded-xl p-5 shadow-[0_2px_8px_rgba(0,0,0,0.06)]"
          style={{ borderTop: `3px solid ${p.color}` }}
        >
          <h4 className="text-[16px] font-bold mb-3" style={{ color: p.color }}>
            {p.company}
          </h4>
          <div className="mb-2.5">
            <div className="text-[11px] uppercase tracking-wide mb-1.5" style={{ color: '#888' }}>
              Strengths
            </div>
            <PillList items={p.strengths} variant="green" />
          </div>
          <div>
            <div className="text-[11px] uppercase tracking-wide mb-1.5" style={{ color: '#888' }}>
              Weaknesses
            </div>
            <PillList items={p.weaknesses} variant="red" />
          </div>
        </div>
      ))}
    </div>
  );
}

function KeyInsights({ insights }: { insights?: string[] }) {
  if (!insights || insights.length === 0) return null;
  return (
    <div
      className="rounded-r-xl p-5 mb-6"
      style={{ background: '#fffbeb', borderLeft: '4px solid #f59e0b' }}
    >
      <div className="text-[16px] font-bold mb-2.5" style={{ color: '#92400e' }}>
        💡 Key Insights
      </div>
      <ul className="list-disc pl-5 space-y-1.5">
        {insights.map((insight, i) => (
          <li key={i} className="text-[14px]" style={{ color: '#78350f', lineHeight: 1.5 }}>
            {insight}
          </li>
        ))}
      </ul>
    </div>
  );
}

function EvalAccordion({
  evaluations,
  summary,
}: {
  evaluations: BenchmarkEvaluation[];
  summary: BenchmarkSummary;
}) {
  const [openIdx, setOpenIdx] = useState<Set<number>>(new Set());

  const toggle = (i: number) => {
    setOpenIdx((prev) => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i);
      else next.add(i);
      return next;
    });
  };

  const { company_a: cA, company_b: cB } = summary;

  return (
    <div className="mb-6">
      <h3 className="text-[14px] font-semibold mb-3" style={{ color: '#555' }}>
        Detailed Evaluations
      </h3>
      {evaluations.map((ev, idx) => {
        const isOpen = openIdx.has(idx);
        const winnerBadge =
          ev.winner === 'company_a' ? (
            <span className="inline-block px-2.5 py-0.5 rounded-xl text-[11px] font-bold uppercase text-white" style={{ background: '#4a6cf7' }}>
              {cA}
            </span>
          ) : ev.winner === 'company_b' ? (
            <span className="inline-block px-2.5 py-0.5 rounded-xl text-[11px] font-bold uppercase text-white" style={{ background: '#f7844a' }}>
              {cB}
            </span>
          ) : (
            <span className="inline-block px-2.5 py-0.5 rounded-xl text-[11px] font-bold uppercase text-white" style={{ background: '#adb5bd' }}>
              Tie
            </span>
          );

        const mA: Partial<CompanyMention> = ev.company_a_mention ?? {};
        const mB: Partial<CompanyMention> = ev.company_b_mention ?? {};

        return (
          <div
            key={idx}
            className="bg-white rounded-xl mb-2 overflow-hidden shadow-[0_1px_4px_rgba(0,0,0,0.05)]"
          >
            <div
              className="flex items-center gap-2.5 px-4.5 py-3.5 cursor-pointer select-none text-[14px] hover:bg-[#f8f9fa]"
              onClick={() => toggle(idx)}
            >
              <span className="font-bold min-w-7" style={{ color: '#555' }}>
                #{idx + 1}
              </span>
              <span
                className="inline-block px-2.5 py-0.5 rounded-xl text-[11px] font-bold uppercase"
                style={{ background: '#e9ecef', color: '#495057' }}
              >
                {(ev.category ?? '').replace(/_/g, ' ')}
              </span>
              {winnerBadge}
              <span className="flex-1 truncate" style={{ color: '#666' }}>
                {ev.prompt_text ?? ''}
              </span>
              <span
                className="text-[12px] transition-transform duration-200"
                style={{
                  color: '#aaa',
                  transform: isOpen ? 'rotate(90deg)' : 'none',
                }}
              >
                ▶
              </span>
            </div>
            {isOpen && (
              <div className="px-4.5 pb-4.5 text-[13px]" style={{ lineHeight: 1.7 }}>
                <div className="mb-3">
                  <div className="text-[11px] uppercase tracking-wide mb-1" style={{ color: '#888' }}>
                    Prompt
                  </div>
                  <p>{ev.prompt_text ?? ''}</p>
                </div>
                <div className="grid grid-cols-2 gap-3 mb-3">
                  {[
                    { label: `${cA} Sentiment`, mention: mA },
                    { label: `${cB} Sentiment`, mention: mB },
                  ].map((col) => (
                    <div key={col.label}>
                      <div className="text-[11px] uppercase tracking-wide mb-1" style={{ color: '#888' }}>
                        {col.label}
                      </div>
                      <strong style={{ color: sentimentColor(col.mention.sentiment ?? 0) }}>
                        {(col.mention.sentiment ?? 0).toFixed(2)}
                      </strong>
                      {col.mention.strengths_mentioned && col.mention.strengths_mentioned.length > 0 && (
                        <div className="mt-1 flex flex-wrap gap-1">
                          {col.mention.strengths_mentioned.map((s, i) => (
                            <span key={i} className="px-2 py-0.5 rounded-full text-[11px]" style={{ background: '#d4edda', color: '#155724' }}>
                              {s}
                            </span>
                          ))}
                        </div>
                      )}
                      {col.mention.weaknesses_mentioned && col.mention.weaknesses_mentioned.length > 0 && (
                        <div className="mt-1 flex flex-wrap gap-1">
                          {col.mention.weaknesses_mentioned.map((s, i) => (
                            <span key={i} className="px-2 py-0.5 rounded-full text-[11px]" style={{ background: '#f8d7da', color: '#721c24' }}>
                              {s}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                {ev.analysis_notes && (
                  <div className="mb-3">
                    <div className="text-[11px] uppercase tracking-wide mb-1" style={{ color: '#888' }}>
                      Analysis Notes
                    </div>
                    <p>{ev.analysis_notes}</p>
                  </div>
                )}
                {ev.llm_response && (
                  <div>
                    <div className="text-[11px] uppercase tracking-wide mb-1" style={{ color: '#888' }}>
                      LLM Response
                    </div>
                    <pre
                      className="rounded-lg p-3 overflow-x-auto text-[12px] whitespace-pre-wrap break-words max-h-[300px] overflow-y-auto"
                      style={{ background: '#f5f7fa' }}
                    >
                      {ev.llm_response}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export function BenchmarkDashboard({ result }: BenchmarkDashboardProps) {
  const { summary, evaluations = [], markdown_report } = result;

  if (!summary) {
    if (markdown_report) {
      return (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="report-content">{markdown_report}</div>
        </div>
      );
    }
    return null;
  }

  return (
    <div>
      <HeroBanner summary={summary} />
      <MetricCards summary={summary} />
      <WinRateBar summary={summary} />
      <SentimentGauges summary={summary} />
      {evaluations.length > 0 && (
        <CategoryBreakdown summary={summary} evaluations={evaluations} />
      )}
      <PerceptionPanels summary={summary} />
      <KeyInsights insights={summary.key_insights} />
      {evaluations.length > 0 && (
        <EvalAccordion evaluations={evaluations} summary={summary} />
      )}
    </div>
  );
}
