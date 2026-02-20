import { useState } from 'react';

interface AddSiteFormProps {
  onAdd: (url: string, maxPages: number) => void;
}

export function AddSiteForm({ onAdd }: AddSiteFormProps) {
  const [url, setUrl] = useState('');
  const [maxPages, setMaxPages] = useState(100);

  const handleSubmit = () => {
    const trimmed = url.trim();
    if (!trimmed) {
      alert('Please enter a URL');
      return;
    }
    try {
      new URL(trimmed);
    } catch {
      alert('Please enter a valid URL');
      return;
    }
    onAdd(trimmed, maxPages);
    setUrl('');
    setMaxPages(100);
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
          <svg
            width="18"
            height="18"
            fill="none"
            stroke="#fff"
            strokeWidth="2.5"
            strokeLinecap="round"
          >
            <line x1="9" y1="3" x2="9" y2="15" />
            <line x1="3" y1="9" x2="15" y2="9" />
          </svg>
        </div>
        <div>
          <div className="text-[16px] font-bold" style={{ color: '#1a1a2e' }}>
            Add Website
          </div>
          <div className="text-[13px]" style={{ color: '#9ca3af' }}>
            Enter a URL to crawl and analyze
          </div>
        </div>
      </div>

      <div className="flex gap-3 items-end flex-wrap">
        <div className="flex-1 min-w-[200px]">
          <label
            className="block text-[13px] font-semibold mb-1"
            style={{ color: '#555' }}
          >
            Website URL
          </label>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
            placeholder="https://example.com"
            className="w-full px-3 py-2.5 rounded-lg text-[14px] focus:outline-none transition-colors"
            style={{ border: '1px solid #d0d7f7' }}
          />
        </div>
        <div className="w-28">
          <label
            className="block text-[13px] font-semibold mb-1"
            style={{ color: '#555' }}
          >
            Max pages
          </label>
          <input
            type="number"
            value={maxPages}
            onChange={(e) => setMaxPages(parseInt(e.target.value) || 100)}
            min={1}
            max={10000}
            className="w-full px-3 py-2.5 rounded-lg text-[14px] focus:outline-none"
            style={{ border: '1px solid #d0d7f7' }}
          />
        </div>
        <div className="w-24">
          <button
            onClick={handleSubmit}
            className="w-full px-4 py-2.5 text-white rounded-xl text-[14px] font-semibold transition-colors"
            style={{ background: '#4a6cf7' }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.background = '#3a5ce5')
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.background = '#4a6cf7')
            }
          >
            Add Site
          </button>
        </div>
      </div>
    </div>
  );
}
