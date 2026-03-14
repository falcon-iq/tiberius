import { useRef, useState } from 'react';
import { api } from '../services/api';

interface BenchmarkFormProps {
  onSubmit: (companyUrl: string, competitorUrls: string[]) => void;
  isSubmitting: boolean;
}

function isValidUrl(value: string): boolean {
  return /^(https?:\/\/)?([\w-]+\.)+[a-z]{2,}(\/\S*)?$/i.test(value.trim());
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

const errorInputStyle: React.CSSProperties = {
  ...inputStyle,
  border: '1px solid rgba(239, 68, 68, 0.5)',
};

const inlineErrorStyle: React.CSSProperties = {
  fontSize: 12,
  color: '#fca5a5',
  marginTop: 4,
};

export function BenchmarkForm({ onSubmit, isSubmitting }: BenchmarkFormProps) {
  const [companyUrl, setCompanyUrl] = useState('');
  const [competitors, setCompetitors] = useState(['']);
  const [error, setError] = useState('');
  const [isSuggesting, setIsSuggesting] = useState(false);
  const [suggestError, setSuggestError] = useState('');
  const [companyUrlError, setCompanyUrlError] = useState('');
  const [competitorErrors, setCompetitorErrors] = useState<string[]>([]);
  const [suggestedForUrl, setSuggestedForUrl] = useState('');
  const firstCompetitorRef = useRef<HTMLInputElement>(null);

  const competitorsAreEmpty = competitors.every((c) => !c.trim());
  const showCompetitors = isValidUrl(companyUrl);

  const validateCompanyUrl = (value: string): boolean => {
    if (value.trim() && !isValidUrl(value)) {
      setCompanyUrlError('Please enter a valid URL (e.g. stripe.com)');
      return false;
    }
    setCompanyUrlError('');
    return true;
  };

  const validateCompetitorUrl = (index: number, value: string): boolean => {
    const errors = [...competitorErrors];
    if (value.trim() && !isValidUrl(value)) {
      errors[index] = 'Please enter a valid URL';
      setCompetitorErrors(errors);
      return false;
    }
    errors[index] = '';
    setCompetitorErrors(errors);
    return true;
  };

  const handleSuggestCompetitors = async () => {
    if (!companyUrl.trim()) {
      setSuggestError('Please enter your website URL first.');
      return;
    }
    if (!isValidUrl(companyUrl)) {
      setCompanyUrlError('Please enter a valid URL (e.g. stripe.com)');
      return;
    }

    setSuggestError('');
    setIsSuggesting(true);
    try {
      const result = await api.suggestCompetitors({ companyUrl: companyUrl.trim() });
      if (result.competitors.length > 0) {
        setCompetitors(result.competitors);
        setCompetitorErrors([]);
        setSuggestedForUrl(companyUrl.trim());
        setTimeout(() => firstCompetitorRef.current?.focus(), 50);
      }
    } catch (err) {
      setSuggestError(err instanceof Error ? err.message : 'Failed to suggest competitors.');
    } finally {
      setIsSuggesting(false);
    }
  };

  const handleCompanyUrlKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && companyUrl.trim() && competitorsAreEmpty && !isSuggesting) {
      e.preventDefault();
      handleSuggestCompetitors();
    }
  };

  const addCompetitor = () => {
    if (competitors.length < 10) {
      setCompetitors([...competitors, '']);
      setCompetitorErrors([...competitorErrors, '']);
    }
  };

  const removeCompetitor = (index: number) => {
    setCompetitors(competitors.filter((_, i) => i !== index));
    setCompetitorErrors(competitorErrors.filter((_, i) => i !== index));
  };

  const updateCompetitor = (index: number, value: string) => {
    const updated = [...competitors];
    updated[index] = value;
    setCompetitors(updated);
    if (competitorErrors[index] && isValidUrl(value)) {
      const errors = [...competitorErrors];
      errors[index] = '';
      setCompetitorErrors(errors);
    }
  };

  const handleSubmit = () => {
    setError('');

    if (!companyUrl.trim()) {
      setError('Please enter your website URL.');
      return;
    }
    if (!isValidUrl(companyUrl)) {
      setCompanyUrlError('Please enter a valid URL (e.g. stripe.com)');
      return;
    }

    const validCompetitors = competitors.map((c) => c.trim()).filter(Boolean);
    if (validCompetitors.length === 0) {
      setError('Please enter at least one competitor URL.');
      return;
    }

    // Validate all non-empty competitor URLs
    let hasInvalid = false;
    const errors = competitors.map((c) => {
      if (c.trim() && !isValidUrl(c)) {
        hasInvalid = true;
        return 'Please enter a valid URL';
      }
      return '';
    });
    if (hasInvalid) {
      setCompetitorErrors(errors);
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
          type="text"
          style={companyUrlError ? errorInputStyle : inputStyle}
          placeholder="https://yourcompany.com"
          value={companyUrl}
          onChange={(e) => {
            const newVal = e.target.value;
            setCompanyUrl(newVal);
            if (companyUrlError && isValidUrl(newVal)) {
              setCompanyUrlError('');
            }
            // Clear stale competitors when company URL changes
            if (suggestedForUrl && newVal.trim() !== suggestedForUrl) {
              setCompetitors(['']);
              setCompetitorErrors([]);
              setSuggestedForUrl('');
            }
          }}
          onBlur={() => validateCompanyUrl(companyUrl)}
          onKeyDown={handleCompanyUrlKeyDown}
          disabled={isSubmitting}
          autoComplete="off"
        />
        {companyUrlError && <div style={inlineErrorStyle}>{companyUrlError}</div>}
        {!companyUrlError && companyUrl.trim() && competitorsAreEmpty && !isSuggesting && showCompetitors && (
          <div style={{ fontSize: 12, color: '#a78bfa', marginTop: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
            <kbd style={{
              padding: '1px 6px',
              background: 'rgba(167, 139, 250, 0.12)',
              border: '1px solid rgba(167, 139, 250, 0.25)',
              borderRadius: 4,
              fontSize: 11,
              fontFamily: 'inherit',
              color: '#c4b5fd',
            }}>Enter</kbd>
            to auto-suggest competitors
          </div>
        )}
      </div>

      {/* Competitors card — shown only when company URL is valid */}
      {showCompetitors && (
      <div style={{ ...cardStyle, animation: 'fadeSlideIn 0.3s ease-out' }}>
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

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
          <label style={{ ...labelStyle, marginBottom: 0 }}>Competitor URLs</label>
          <button
            onClick={handleSuggestCompetitors}
            disabled={isSubmitting || isSuggesting || !companyUrl.trim()}
            style={{
              padding: '6px 14px',
              border: '1px solid rgba(168, 85, 247, 0.3)',
              borderRadius: 8,
              background: isSuggesting
                ? 'rgba(168, 85, 247, 0.15)'
                : 'linear-gradient(135deg, rgba(99,102,241,0.12), rgba(168,85,247,0.12))',
              color: !companyUrl.trim() ? '#52525b' : '#c084fc',
              fontSize: 12,
              fontWeight: 600,
              cursor: !companyUrl.trim() || isSuggesting ? 'not-allowed' : 'pointer',
              opacity: !companyUrl.trim() ? 0.5 : 1,
              fontFamily: 'inherit',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" style={{ width: 14, height: 14 }}>
              <path d="M12 2a4 4 0 0 0-4 4c0 2 2 3 2 6h4c0-3 2-4 2-6a4 4 0 0 0-4-4z" />
              <path d="M10 18h4M11 22h2" />
            </svg>
            {isSuggesting ? 'Finding competitors...' : 'Suggest with AI'}
          </button>
        </div>
        {suggestError && (
          <div style={{ fontSize: 12, color: '#fca5a5', marginBottom: 8 }}>{suggestError}</div>
        )}
        {isSuggesting && (
          <div style={{ marginBottom: 10 }}>
            {Array.from({ length: 5 }).map((_, i) => (
              <div
                key={i}
                style={{
                  height: 44,
                  background: 'rgba(9, 9, 11, 0.6)',
                  border: '1px solid rgba(63, 63, 70, 0.6)',
                  borderRadius: 10,
                  marginBottom: 10,
                  animation: 'pulse 1.5s ease-in-out infinite',
                  animationDelay: `${i * 0.1}s`,
                  opacity: 0.6,
                }}
              />
            ))}
            <style>{`@keyframes pulse { 0%, 100% { opacity: 0.4; } 50% { opacity: 0.7; } }`}</style>
            <div style={{ fontSize: 12, color: '#a78bfa', textAlign: 'center' }}>
              Finding competitors...
            </div>
          </div>
        )}
        {!isSuggesting && competitors.map((url, i) => (
          <div key={i} style={{ marginBottom: 10 }}>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', animation: 'fadeSlideIn 0.25s ease-out' }}>
              <input
                ref={i === 0 ? firstCompetitorRef : undefined}
                type="text"
                style={{ ...(competitorErrors[i] ? errorInputStyle : inputStyle), flex: 1 }}
                placeholder={`https://competitor${i + 1}.com`}
                value={url}
                onChange={(e) => updateCompetitor(i, e.target.value)}
                onBlur={() => validateCompetitorUrl(i, url)}
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
            {competitorErrors[i] && <div style={inlineErrorStyle}>{competitorErrors[i]}</div>}
          </div>
        ))}

        {!isSuggesting && (
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
        )}
        {!isSuggesting && (
        <div style={{ fontSize: 12, color: '#52525b', textAlign: 'right', marginTop: 6 }}>
          {competitors.length} of 10 competitors
        </div>
        )}
      </div>
      )}

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

      {showCompetitors && (
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
      )}
    </>
  );
}
