import { useState } from 'react';
import type { IndustryBenchmarkDetail, IndustryCompanyEntry } from '@app-types/api';

interface Props {
  benchmark: IndustryBenchmarkDetail;
  onBack: () => void;
}

function CompanyPill({ company, selected, onClick }: {
  company: IndustryCompanyEntry;
  selected: boolean;
  onClick: () => void;
}) {
  const [logoErr, setLogoErr] = useState(false);
  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '8px 14px',
        borderRadius: 10,
        border: selected ? '1px solid rgba(99, 102, 241, 0.5)' : '1px solid rgba(63, 63, 70, 0.4)',
        background: selected ? 'rgba(99, 102, 241, 0.15)' : 'rgba(24, 24, 32, 0.6)',
        color: selected ? '#e0e7ff' : '#71717a',
        cursor: 'pointer',
        fontFamily: 'inherit',
        fontSize: '0.8rem',
        fontWeight: selected ? 600 : 400,
        transition: 'all 0.2s ease',
        flexShrink: 0,
        whiteSpace: 'nowrap',
      }}
    >
      {!logoErr && company.logoUrl ? (
        <img
          src={company.logoUrl}
          alt=""
          onError={() => setLogoErr(true)}
          style={{ width: 20, height: 20, borderRadius: 5, objectFit: 'contain', background: '#fff' }}
        />
      ) : (
        <div style={{
          width: 20, height: 20, borderRadius: 5,
          background: 'linear-gradient(135deg, #6366f1, #a855f7)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 11, fontWeight: 700, color: '#fff',
        }}>
          {company.companyName.charAt(0)}
        </div>
      )}
      {company.companyName}
    </button>
  );
}

function SectionHeader({ color, label, collapsed, onToggle }: {
  color: string;
  label: string;
  collapsed: boolean;
  onToggle: () => void;
}) {
  return (
    <div
      onClick={onToggle}
      style={{
        display: 'flex', alignItems: 'center', gap: 8, marginBottom: collapsed ? 0 : 16,
        cursor: 'pointer', userSelect: 'none',
      }}
    >
      <div style={{ width: 8, height: 8, borderRadius: '50%', background: color }} />
      <span style={{
        fontSize: '0.9rem', fontWeight: 600, color,
        textTransform: 'uppercase', letterSpacing: '0.05em', flex: 1,
      }}>
        {label}
      </span>
      <svg
        viewBox="0 0 24 24" fill="none" strokeWidth="2"
        strokeLinecap="round" strokeLinejoin="round" stroke={color}
        style={{ width: 16, height: 16, transform: collapsed ? 'rotate(-90deg)' : 'rotate(0)', transition: 'transform 0.2s' }}
      >
        <path d="M6 9l6 6 6-6" />
      </svg>
    </div>
  );
}

export function IndustryDetailView({ benchmark, onBack }: Props) {
  const [selectedNames, setSelectedNames] = useState<Set<string>>(
    () => new Set(benchmark.companies.map(c => c.companyName))
  );
  const [collapsedSections, setCollapsedSections] = useState<Set<string>>(() => new Set());

  const toggleCompany = (name: string) => {
    setSelectedNames(prev => {
      const next = new Set(prev);
      if (next.has(name)) {
        if (next.size > 1) next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  };

  const toggleSection = (section: string) => {
    setCollapsedSections(prev => {
      const next = new Set(prev);
      if (next.has(section)) next.delete(section);
      else next.add(section);
      return next;
    });
  };

  const selected = benchmark.companies.filter(c => selectedNames.has(c.companyName));

  // Collect all unique fact labels across selected companies
  const allFactLabels: string[] = [];
  const seenLabels = new Set<string>();
  for (const c of selected) {
    for (const f of (c.keyFacts || [])) {
      if (f.label !== 'Wikipedia' && !seenLabels.has(f.label)) {
        seenLabels.add(f.label);
        allFactLabels.push(f.label);
      }
    }
  }

  const cardStyle: React.CSSProperties = {
    background: 'rgba(24, 24, 32, 0.8)',
    border: '1px solid rgba(63, 63, 70, 0.5)',
    borderRadius: 16,
    padding: 24,
    backdropFilter: 'blur(12px)',
  };

  return (
    <div style={{ animation: 'fadeSlideIn 0.3s ease-out' }}>
      {/* Back button */}
      <button
        onClick={onBack}
        style={{
          background: 'rgba(63, 63, 70, 0.3)', border: '1px solid rgba(63, 63, 70, 0.5)',
          borderRadius: 10, padding: '8px 16px', color: '#a1a1aa', cursor: 'pointer',
          display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem',
          marginBottom: 24, transition: 'all 0.2s ease', fontFamily: 'inherit',
        }}
        onMouseEnter={e => { e.currentTarget.style.background = 'rgba(63, 63, 70, 0.5)'; e.currentTarget.style.color = '#f4f4f5'; }}
        onMouseLeave={e => { e.currentTarget.style.background = 'rgba(63, 63, 70, 0.3)'; e.currentTarget.style.color = '#a1a1aa'; }}
      >
        <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" stroke="currentColor" style={{ width: 16, height: 16 }}>
          <path d="M19 12H5M12 19l-7-7 7-7" />
        </svg>
        Back to Industries
      </button>

      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
          <h2 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 700, color: '#f4f4f5' }}>
            {benchmark.industryName}
          </h2>
          <span style={{
            background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8',
            fontSize: '0.75rem', fontWeight: 600, padding: '4px 10px', borderRadius: 6,
          }}>
            {benchmark.country}
          </span>
        </div>
        <p style={{ margin: 0, color: '#71717a', fontSize: '0.9rem' }}>
          {benchmark.companies.length} companies analyzed
          {benchmark.generatedAt && (
            <span> &middot; Generated {new Date(benchmark.generatedAt).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}</span>
          )}
        </p>
      </div>

      {/* Company selector pills */}
      <div style={{
        display: 'flex', gap: 8, marginBottom: 28, flexWrap: 'wrap',
      }}>
        {benchmark.companies.map(c => (
          <CompanyPill
            key={c.companyName}
            company={c}
            selected={selectedNames.has(c.companyName)}
            onClick={() => toggleCompany(c.companyName)}
          />
        ))}
      </div>

      {/* Section 1: Key Facts comparison table */}
      {allFactLabels.length > 0 && (
        <div style={{ ...cardStyle, marginBottom: 16 }}>
          <SectionHeader color="#60a5fa" label="Key Facts" collapsed={collapsedSections.has('facts')} onToggle={() => toggleSection('facts')} />
          {!collapsedSections.has('facts') && (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left', padding: '8px 12px', color: '#52525b', fontWeight: 500, borderBottom: '1px solid rgba(63,63,70,0.4)', minWidth: 100 }} />
                    {selected.map(c => (
                      <th key={c.companyName} style={{ textAlign: 'center', padding: '8px 12px', color: '#a1a1aa', fontWeight: 600, borderBottom: '1px solid rgba(63,63,70,0.4)', minWidth: 120 }}>
                        {c.companyName}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {allFactLabels.map(label => (
                    <tr key={label}>
                      <td style={{ padding: '10px 12px', color: '#71717a', borderBottom: '1px solid rgba(63,63,70,0.2)' }}>
                        {label}
                      </td>
                      {selected.map(c => {
                        const fact = (c.keyFacts || []).find(f => f.label === label);
                        return (
                          <td key={c.companyName} style={{ textAlign: 'center', padding: '10px 12px', borderBottom: '1px solid rgba(63,63,70,0.2)' }}>
                            {fact ? (
                              <div>
                                <span style={{ color: '#f4f4f5', fontWeight: 500 }}>{fact.value}</span>
                                {fact.sourceUrl && (
                                  <div>
                                    <a href={fact.sourceUrl} target="_blank" rel="noopener noreferrer"
                                      style={{ fontSize: '0.65rem', color: '#60a5fa', textDecoration: 'none', borderBottom: '1px dotted rgba(96,165,250,0.4)' }}>
                                      {fact.source}
                                    </a>
                                  </div>
                                )}
                              </div>
                            ) : (
                              <span style={{ color: '#3f3f46' }}>&mdash;</span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Section 2: Strengths */}
      <div style={{ ...cardStyle, marginBottom: 16 }}>
        <SectionHeader color="#4ade80" label="Strengths" collapsed={collapsedSections.has('strengths')} onToggle={() => toggleSection('strengths')} />
        {!collapsedSections.has('strengths') && (
          <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.min(selected.length, 3)}, 1fr)`, gap: 12 }}>
            {selected.map(c => (
              <div key={c.companyName}>
                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#a1a1aa', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <CompanyLogo company={c} size={18} />
                  {c.companyName}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {c.strengths.map((s, i) => (
                    <div key={i} style={{
                      background: 'rgba(74, 222, 128, 0.06)', border: '1px solid rgba(74, 222, 128, 0.15)',
                      borderRadius: 8, padding: '10px 12px',
                    }}>
                      <div style={{ fontWeight: 600, fontSize: '0.8rem', color: '#f4f4f5', marginBottom: 3 }}>{s.title}</div>
                      <div style={{ fontSize: '0.75rem', color: '#a1a1aa', lineHeight: 1.5 }}>{s.detail}</div>
                    </div>
                  ))}
                  {c.strengths.length === 0 && <span style={{ color: '#3f3f46', fontSize: '0.8rem' }}>No data</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Section 3: Areas for Improvement */}
      <div style={{ ...cardStyle, marginBottom: 16 }}>
        <SectionHeader color="#f59e0b" label="Areas for Improvement" collapsed={collapsedSections.has('improvements')} onToggle={() => toggleSection('improvements')} />
        {!collapsedSections.has('improvements') && (
          <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.min(selected.length, 3)}, 1fr)`, gap: 12 }}>
            {selected.map(c => (
              <div key={c.companyName}>
                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#a1a1aa', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <CompanyLogo company={c} size={18} />
                  {c.companyName}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {c.improvements.map((imp, i) => (
                    <div key={i} style={{
                      background: 'rgba(245, 158, 11, 0.06)', border: '1px solid rgba(245, 158, 11, 0.15)',
                      borderRadius: 8, padding: '10px 12px',
                    }}>
                      <div style={{ fontWeight: 600, fontSize: '0.8rem', color: '#f4f4f5', marginBottom: 3 }}>{imp.title}</div>
                      <div style={{ fontSize: '0.75rem', color: '#a1a1aa', lineHeight: 1.5 }}>{imp.detail}</div>
                    </div>
                  ))}
                  {c.improvements.length === 0 && <span style={{ color: '#3f3f46', fontSize: '0.8rem' }}>No data</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Section 4: Testimonials (only if any company has them) */}
      {selected.some(c => c.testimonials.length > 0) && (
        <div style={{ ...cardStyle, marginBottom: 16 }}>
          <SectionHeader color="#818cf8" label="Customer Voices" collapsed={collapsedSections.has('testimonials')} onToggle={() => toggleSection('testimonials')} />
          {!collapsedSections.has('testimonials') && (
            <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.min(selected.length, 3)}, 1fr)`, gap: 12 }}>
              {selected.map(c => (
                <div key={c.companyName}>
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#a1a1aa', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
                    <CompanyLogo company={c} size={18} />
                    {c.companyName}
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {c.testimonials.map((t, i) => (
                      <div key={i} style={{
                        background: 'rgba(129, 140, 248, 0.06)', border: '1px solid rgba(129, 140, 248, 0.15)',
                        borderRadius: 8, padding: '10px 12px', borderLeft: '3px solid #818cf8',
                      }}>
                        <div style={{ fontSize: '0.8rem', color: '#d4d4d8', fontStyle: 'italic', lineHeight: 1.5, marginBottom: 6 }}>
                          &ldquo;{t.quote}&rdquo;
                        </div>
                        <div style={{ fontSize: '0.7rem', color: '#71717a' }}>
                          {t.authorRole}{t.authorRole && t.source && ' — '}{t.source}
                        </div>
                      </div>
                    ))}
                    {c.testimonials.length === 0 && <span style={{ color: '#3f3f46', fontSize: '0.8rem' }}>No testimonials</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Wikipedia links row */}
      <div style={{ ...cardStyle }}>
        <div style={{ fontSize: '0.8rem', color: '#52525b', marginBottom: 12 }}>Company Links</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {selected.map(c => {
            const wikiLink = (c.keyFacts || []).find(f => f.label === 'Wikipedia');
            return (
              <a
                key={c.companyName}
                href={wikiLink?.sourceUrl || c.companyUrl}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  padding: '6px 12px', borderRadius: 8,
                  background: 'rgba(63, 63, 70, 0.2)', border: '1px solid rgba(63, 63, 70, 0.3)',
                  color: '#a1a1aa', fontSize: '0.75rem', textDecoration: 'none',
                  transition: 'all 0.2s ease',
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(96,165,250,0.4)'; e.currentTarget.style.color = '#60a5fa'; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = 'rgba(63,63,70,0.3)'; e.currentTarget.style.color = '#a1a1aa'; }}
              >
                <CompanyLogo company={c} size={16} />
                {c.companyName}
                <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" stroke="currentColor" style={{ width: 12, height: 12 }}>
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6M15 3h6v6M10 14L21 3" />
                </svg>
              </a>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function CompanyLogo({ company, size }: { company: IndustryCompanyEntry; size: number }) {
  const [err, setErr] = useState(false);
  if (!err && company.logoUrl) {
    return (
      <img
        src={company.logoUrl}
        alt=""
        onError={() => setErr(true)}
        style={{ width: size, height: size, borderRadius: size * 0.25, objectFit: 'contain', background: '#fff', flexShrink: 0 }}
      />
    );
  }
  return (
    <div style={{
      width: size, height: size, borderRadius: size * 0.25, flexShrink: 0,
      background: 'linear-gradient(135deg, #6366f1, #a855f7)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: size * 0.5, fontWeight: 700, color: '#fff',
    }}>
      {company.companyName.charAt(0)}
    </div>
  );
}
