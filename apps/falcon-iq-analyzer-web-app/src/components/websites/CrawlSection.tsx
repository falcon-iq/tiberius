import { useState } from 'react';
import type { LocalSite, CrawlJobStatus } from '@app-types/api';
import { ProgressBar } from '@components/shared/ProgressBar';

interface CrawlSectionProps {
  site: LocalSite;
  crawlJobData: CrawlJobStatus | undefined;
  crawlPct: number;
  crawlMessage: string;
  crawlError: string | null;
  onStartCrawl: (maxPages: number) => void;
}

export function CrawlSection({
  site,
  crawlJobData,
  crawlPct,
  crawlMessage,
  crawlError,
  onStartCrawl,
}: CrawlSectionProps) {
  const [maxPages, setMaxPages] = useState(site.maxPages || 100);

  if (site.status === 'crawling') {
    return (
      <div className="py-2">
        <div
          className="text-[11px] font-bold uppercase tracking-widest mb-1.5"
          style={{ color: '#9ca3af' }}
        >
          Crawling in progress
        </div>
        <ProgressBar pct={crawlPct} message={crawlMessage} />
      </div>
    );
  }

  if (site.status === 'analyzing') {
    return null;
  }

  const isDisabled = !!crawlJobData && crawlJobData.status === 'running';

  return (
    <div className="py-3.5">
      <div
        className="text-[11px] font-bold uppercase tracking-widest mb-1.5"
        style={{ color: '#9ca3af' }}
      >
        Crawl
      </div>
      <div className="flex gap-2.5 items-end flex-wrap">
        <input
          type="number"
          value={maxPages}
          onChange={(e) => setMaxPages(parseInt(e.target.value) || 100)}
          min={1}
          max={10000}
          placeholder="Max pages"
          className="w-28 px-3 py-2 rounded-lg text-[13px] focus:outline-none"
          style={{ border: '1px solid #ddd' }}
        />
        <button
          onClick={() => onStartCrawl(maxPages)}
          disabled={isDisabled}
          className="px-3.5 py-2 text-white rounded-lg text-[12px] font-semibold transition-colors disabled:cursor-not-allowed"
          style={{
            background: isDisabled ? '#b0b8d1' : '#4a6cf7',
          }}
          onMouseEnter={(e) => {
            if (!isDisabled) (e.currentTarget as HTMLElement).style.background = '#3a5ce5';
          }}
          onMouseLeave={(e) => {
            if (!isDisabled) (e.currentTarget as HTMLElement).style.background = '#4a6cf7';
          }}
        >
          ▶ Crawl
        </button>
      </div>
      {crawlError && (
        <p className="text-[13px] mt-2" style={{ color: '#dc3545' }}>
          {crawlError}
        </p>
      )}
    </div>
  );
}
