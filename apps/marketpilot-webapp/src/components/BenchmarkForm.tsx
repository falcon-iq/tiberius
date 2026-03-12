import { useState } from 'react';

interface BenchmarkFormProps {
  onSubmit: (companyUrl: string, competitorUrls: string[]) => void;
  isSubmitting: boolean;
}

const cardStyle: React.CSSProperties = {
  background: 'rgba(24, 24, 32, 0.8)',
  border: '1px solid rgba(63, 63, 70, 0.5)',
  borderRadius: 16,
  padding: 32,
  marginBottom: 24,
  backdropFilter: 'blur(12px)',
};

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: 13,
  fontWeight: 600,
  color: '#a1a1aa',
  marginBottom: 6,
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '12px 16px',
  background: 'rgba(9, 9, 11, 0.6)',
  border: '1px solid rgba(63, 63, 70, 0.6)',
  borderRadius: 10,
  color: '#f4f4f5',
  fontSize: 14,
  fontFamily: 'inherit',
  outline: 'none',
};

export function BenchmarkForm({ onSubmit, isSubmitting }: BenchmarkFormProps) {
  const [companyUrl, setCompanyUrl] = useState('');
  const [competitors, setCompetitors] = useState(['']);
  const [error, setError] = useState('');

  const addCompetitor = () => {
    if (competitors.length < 10) {
      setCompetitors([...competitors, '']);
    }
  };

  const removeCompetitor = (index: number) => {
    setCompetitors(competitors.filter((_, i) => i !== index));
  };

  const updateCompetitor = (index: number, value: string) => {
    const updated = [...competitors];
    updated[index] = value;
    setCompetitors(updated);
  };

  const handleSubmit = () => {
    setError('');

    if (!companyUrl.trim()) {
      setError('Please enter your website URL.');
      return;
    }

    const validCompetitors = competitors.map((c) => c.trim()).filter(Boolean);
    if (validCompetitors.length === 0) {
      setError('Please enter at least one competitor URL.');
      return;
    }

    onSubmit(companyUrl.trim(), validCompetitors);
  };

  return (
    <>
      {/* Company card */}
      <div style={cardStyle}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: 12,
              background: 'linear-gradient(135deg, rgba(99,102,241,0.15), rgba(168,85,247,0.15))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="#818cf8" strokeWidth="2" strokeLinecap="round" style={{ width: 20, height: 20 }}>
              <circle cx="12" cy="12" r="10" />
              <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
            </svg>
          </div>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#f4f4f5' }}>Your Website</div>
            <div style={{ fontSize: 13, color: '#71717a', marginTop: 2 }}>Enter the website you want to benchmark</div>
          </div>
        </div>
        <label style={labelStyle} htmlFor="companyUrl">Website URL</label>
        <input
          id="companyUrl"
          type="url"
          style={inputStyle}
          placeholder="https://yourcompany.com"
          value={companyUrl}
          onChange={(e) => setCompanyUrl(e.target.value)}
          disabled={isSubmitting}
          autoComplete="off"
        />
      </div>

      {/* Competitors card */}
      <div style={cardStyle}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: 12,
              background: 'linear-gradient(135deg, rgba(168,85,247,0.15), rgba(236,72,153,0.15))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="#c084fc" strokeWidth="2" strokeLinecap="round" style={{ width: 20, height: 20 }}>
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
          </div>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#f4f4f5' }}>Competitors</div>
            <div style={{ fontSize: 13, color: '#71717a', marginTop: 2 }}>Add 1 to 10 competitor websites to compare against</div>
          </div>
        </div>

        <label style={labelStyle}>Competitor URLs</label>
        {competitors.map((url, i) => (
          <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 10, alignItems: 'center', animation: 'fadeSlideIn 0.25s ease-out' }}>
            <input
              type="url"
              style={{ ...inputStyle, flex: 1 }}
              placeholder={`https://competitor${i + 1}.com`}
              value={url}
              onChange={(e) => updateCompetitor(i, e.target.value)}
              disabled={isSubmitting}
              autoComplete="off"
            />
            {competitors.length > 1 && (
              <button
                onClick={() => removeCompetitor(i)}
                disabled={isSubmitting}
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: 8,
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  background: 'rgba(239, 68, 68, 0.08)',
                  color: '#ef4444',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  fontSize: 18,
                  lineHeight: 1,
                }}
              >
                &times;
              </button>
            )}
          </div>
        ))}

        <button
          onClick={addCompetitor}
          disabled={isSubmitting || competitors.length >= 10}
          style={{
            width: '100%',
            padding: 10,
            border: '1px dashed rgba(99, 102, 241, 0.3)',
            borderRadius: 10,
            background: 'transparent',
            color: '#818cf8',
            fontSize: 13,
            fontWeight: 600,
            cursor: competitors.length >= 10 ? 'not-allowed' : 'pointer',
            opacity: competitors.length >= 10 ? 0.4 : 1,
            fontFamily: 'inherit',
            marginTop: 4,
          }}
        >
          + Add Competitor
        </button>
        <div style={{ fontSize: 12, color: '#52525b', textAlign: 'right', marginTop: 6 }}>
          {competitors.length} of 10 competitors
        </div>
      </div>

      {error && (
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
          {error}
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={isSubmitting}
        style={{
          width: '100%',
          padding: '14px 24px',
          border: 'none',
          borderRadius: 12,
          background: isSubmitting ? 'rgba(99, 102, 241, 0.5)' : 'linear-gradient(135deg, #6366f1, #7c3aed)',
          color: '#fff',
          fontSize: 15,
          fontWeight: 700,
          cursor: isSubmitting ? 'not-allowed' : 'pointer',
          fontFamily: 'inherit',
          marginTop: 8,
        }}
      >
        {isSubmitting ? 'Starting...' : 'Launch Benchmark Analysis'}
      </button>
    </>
  );
}
