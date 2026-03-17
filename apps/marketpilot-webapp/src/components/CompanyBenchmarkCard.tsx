import { useState } from 'react';
import type { IndustryCompanyEntry } from '@app-types/api';

interface Props {
  company: IndustryCompanyEntry;
  index: number;
}

export function CompanyBenchmarkCard({ company, index }: Props) {
  const [expanded, setExpanded] = useState(true);
  const [logoError, setLogoError] = useState(false);

  return (
    <div
      style={{
        background: 'rgba(24, 24, 32, 0.8)',
        border: '1px solid rgba(63, 63, 70, 0.5)',
        borderRadius: 16,
        padding: 24,
        backdropFilter: 'blur(12px)',
        animation: `fadeSlideIn 0.3s ease-out ${index * 0.1}s both`,
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: expanded ? 20 : 0,
          cursor: 'pointer',
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {logoError || !company.logoUrl ? (
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: 10,
                background: 'linear-gradient(135deg, #6366f1, #a855f7)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 14,
                fontWeight: 700,
                color: '#fff',
              }}
            >
              {company.companyName.charAt(0).toUpperCase()}
            </div>
          ) : (
            <img
              src={company.logoUrl}
              alt={company.companyName}
              onError={() => setLogoError(true)}
              style={{
                width: 36,
                height: 36,
                borderRadius: 10,
                objectFit: 'contain',
                background: '#fff',
              }}
            />
          )}
          <div>
            <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600, color: '#f4f4f5' }}>
              {company.companyName}
            </h3>
            <span style={{ fontSize: '0.8rem', color: '#71717a' }}>{company.companyUrl}</span>
          </div>
        </div>
        <svg
          viewBox="0 0 24 24"
          fill="none"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          stroke="#a1a1aa"
          style={{
            width: 20,
            height: 20,
            transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.2s ease',
          }}
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </div>

      {expanded && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Key Facts */}
          {company.keyFacts && company.keyFacts.length > 0 && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#60a5fa' }} />
                <span style={{
                  fontSize: '0.85rem', fontWeight: 600, color: '#60a5fa',
                  textTransform: 'uppercase', letterSpacing: '0.05em',
                }}>
                  Key Facts
                </span>
              </div>
              <div style={{
                background: 'rgba(96, 165, 250, 0.08)',
                border: '1px solid rgba(96, 165, 250, 0.2)',
                borderRadius: 10,
                padding: '4px 16px',
              }}>
                {company.keyFacts.map((fact, i) => (
                  <div
                    key={i}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'baseline',
                      padding: '10px 0',
                      borderBottom: i < company.keyFacts.length - 1 ? '1px solid rgba(63, 63, 70, 0.3)' : 'none',
                    }}
                  >
                    <span style={{ fontSize: '0.85rem', color: '#71717a', minWidth: 120 }}>
                      {fact.label}
                    </span>
                    <div style={{ textAlign: 'right' }}>
                      <span style={{ fontSize: '0.9rem', color: '#f4f4f5', fontWeight: 500 }}>
                        {fact.value}
                      </span>
                      {fact.source && (
                        <div style={{ marginTop: 2 }}>
                          {fact.sourceUrl ? (
                            <a
                              href={fact.sourceUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{
                                fontSize: '0.7rem', color: '#60a5fa', textDecoration: 'none',
                                borderBottom: '1px dotted rgba(96, 165, 250, 0.4)',
                              }}
                              onMouseEnter={(e) => { e.currentTarget.style.color = '#93c5fd'; }}
                              onMouseLeave={(e) => { e.currentTarget.style.color = '#60a5fa'; }}
                            >
                              {fact.source}
                            </a>
                          ) : (
                            <span style={{ fontSize: '0.7rem', color: '#52525b' }}>{fact.source}</span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Strengths */}
          {company.strengths.length > 0 && (
            <div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  marginBottom: 12,
                }}
              >
                <div
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    background: '#4ade80',
                  }}
                />
                <span
                  style={{
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    color: '#4ade80',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                  }}
                >
                  Strengths
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {company.strengths.map((s, i) => (
                  <div
                    key={i}
                    style={{
                      background: 'rgba(74, 222, 128, 0.08)',
                      border: '1px solid rgba(74, 222, 128, 0.2)',
                      borderRadius: 10,
                      padding: '12px 16px',
                    }}
                  >
                    <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#f4f4f5', marginBottom: 4 }}>
                      {s.title}
                    </div>
                    <div style={{ fontSize: '0.85rem', color: '#a1a1aa', lineHeight: 1.5 }}>
                      {s.detail}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Improvements */}
          {company.improvements.length > 0 && (
            <div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  marginBottom: 12,
                }}
              >
                <div
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    background: '#f59e0b',
                  }}
                />
                <span
                  style={{
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    color: '#f59e0b',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                  }}
                >
                  Areas for Improvement
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {company.improvements.map((imp, i) => (
                  <div
                    key={i}
                    style={{
                      background: 'rgba(245, 158, 11, 0.08)',
                      border: '1px solid rgba(245, 158, 11, 0.2)',
                      borderRadius: 10,
                      padding: '12px 16px',
                    }}
                  >
                    <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#f4f4f5', marginBottom: 4 }}>
                      {imp.title}
                    </div>
                    <div style={{ fontSize: '0.85rem', color: '#a1a1aa', lineHeight: 1.5 }}>
                      {imp.detail}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Testimonials */}
          {company.testimonials.length > 0 && (
            <div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  marginBottom: 12,
                }}
              >
                <div
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    background: '#818cf8',
                  }}
                />
                <span
                  style={{
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    color: '#818cf8',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                  }}
                >
                  Customer Voices
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {company.testimonials.map((t, i) => (
                  <div
                    key={i}
                    style={{
                      background: 'rgba(129, 140, 248, 0.08)',
                      border: '1px solid rgba(129, 140, 248, 0.2)',
                      borderRadius: 10,
                      padding: '12px 16px',
                      borderLeft: '3px solid #818cf8',
                    }}
                  >
                    <div
                      style={{
                        fontSize: '0.9rem',
                        color: '#d4d4d8',
                        fontStyle: 'italic',
                        lineHeight: 1.6,
                        marginBottom: 8,
                      }}
                    >
                      &ldquo;{t.quote}&rdquo;
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#71717a' }}>
                      {t.authorRole && <span>{t.authorRole}</span>}
                      {t.authorRole && t.source && <span> &mdash; </span>}
                      {t.source && <span>{t.source}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
