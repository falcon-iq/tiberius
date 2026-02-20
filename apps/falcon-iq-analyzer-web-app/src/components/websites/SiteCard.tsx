import { useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type { LocalSite, Analysis } from '@app-types/api';
import { api } from '@services/api';
import { useCrawlJob } from '@hooks/use-crawl-job';
import { useAnalyzeJob } from '@hooks/use-analyze-job';
import { StatusBadge } from '@components/shared/StatusBadge';
import { CrawlSection } from './CrawlSection';
import { AnalyzeSection } from './AnalyzeSection';
import { AnalysisHistory } from './AnalysisHistory';

interface SiteCardProps {
  site: LocalSite;
  analyses: Analysis[];
  onUpdate: (domain: string, updates: Partial<LocalSite>) => void;
  onRemove: (domain: string) => Promise<void>;
  onAnalysisDeleted: () => void;
}

export function SiteCard({ site, analyses, onUpdate, onRemove, onAnalysisDeleted }: SiteCardProps) {
  const [crawlJobId, setCrawlJobId] = useState<string | null>(null);
  const [crawlError, setCrawlError] = useState<string | null>(null);
  const [analyzeJobId, setAnalyzeJobId] = useState<string | null>(null);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);
  const [latestAnalysisReport, setLatestAnalysisReport] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: crawlJobData } = useCrawlJob(crawlJobId);
  const { data: analyzeJobData } = useAnalyzeJob(analyzeJobId);

  // React to crawl job status changes
  const crawlStatus = crawlJobData?.status;
  useEffect(() => {
    if (!crawlStatus) return;
    if (crawlStatus === 'completed' && crawlJobData) {
      onUpdate(site.domain, {
        status: 'crawled',
        directory: crawlJobData.output_dir,
        page_count: crawlJobData.page_count,
      });
      setCrawlJobId(null);
      setCrawlError(null);
    } else if (crawlStatus === 'failed') {
      onUpdate(site.domain, { status: 'failed' });
      setCrawlJobId(null);
      setCrawlError(crawlJobData?.error ?? 'Crawl failed');
    }
  }, [crawlStatus]); // eslint-disable-line react-hooks/exhaustive-deps

  // React to analyze job status changes
  const analyzeStatus = analyzeJobData?.status;
  useEffect(() => {
    if (!analyzeStatus) return;
    if (analyzeStatus === 'completed') {
      onUpdate(site.domain, { status: 'analyzed' });
      setAnalyzeJobId(null);
      setAnalyzeError(null);
      if (analyzeJobData?.result?.markdown_report) {
        setLatestAnalysisReport(analyzeJobData.result.markdown_report);
      }
      queryClient.invalidateQueries({ queryKey: ['analyses'] });
      queryClient.invalidateQueries({ queryKey: ['sites'] });
    } else if (analyzeStatus === 'failed') {
      onUpdate(site.domain, { status: 'crawled' });
      setAnalyzeJobId(null);
      setAnalyzeError(analyzeJobData?.error ?? 'Analysis failed');
    }
  }, [analyzeStatus]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleStartCrawl = async (maxPages: number) => {
    setCrawlError(null);
    onUpdate(site.domain, { status: 'crawling', maxPages });
    try {
      const { job_id } = await api.startCrawl(site.url, maxPages);
      setCrawlJobId(job_id);
    } catch (e) {
      onUpdate(site.domain, { status: 'failed' });
      setCrawlError((e as Error).message);
    }
  };

  const handleStartAnalyze = async (companyName: string) => {
    if (!site.directory) return;
    setAnalyzeError(null);
    onUpdate(site.domain, { status: 'analyzing' });
    try {
      const { job_id } = await api.startAnalyze(site.directory, companyName, site.domain);
      setAnalyzeJobId(job_id);
    } catch (e) {
      onUpdate(site.domain, { status: 'crawled' });
      setAnalyzeError((e as Error).message);
    }
  };

  const handleDeleteAnalysis = async (jobId: string) => {
    if (!confirm('Delete this analysis? This cannot be undone.')) return;
    try {
      await api.deleteAnalysis(jobId);
      onAnalysisDeleted();
    } catch (e) {
      alert('Failed to delete: ' + (e as Error).message);
    }
  };

  // Filter analyses for this site
  const siteDomain = site.domain.replace(/^www\./, '').toLowerCase();
  const siteAnalyses = analyses.filter((a) => {
    if (a.domain) {
      const aDomain = a.domain.replace(/^www\./, '').toLowerCase();
      if (aDomain === siteDomain) return true;
    }
    if (a.crawl_directory && site.directory) {
      const d1 = a.crawl_directory.replace(/\/+$/, '');
      const d2 = site.directory.replace(/\/+$/, '');
      if (d1 === d2) return true;
    }
    return (a.crawl_directory ?? '').toLowerCase().includes(siteDomain);
  });

  // Crawl progress
  const crawlPct = crawlJobData
    ? crawlJobData.status === 'completed'
      ? 100
      : site.maxPages > 0
        ? Math.min(95, (crawlJobData.page_count / site.maxPages) * 100)
        : 10
    : 5;
  const crawlMessage = crawlJobData?.progress ?? crawlJobData?.status ?? 'Crawling...';

  // Analyze progress
  const analyzeStepMatch = analyzeJobData?.progress?.match(/step\s*(\d+)/i);
  const analyzePct = analyzeJobData
    ? analyzeJobData.status === 'completed'
      ? 100
      : analyzeStepMatch
        ? Math.min(95, (parseInt(analyzeStepMatch[1]) / 6) * 100)
        : 10
    : 5;
  const analyzeMessage = analyzeJobData?.progress ?? analyzeJobData?.status ?? 'Analyzing...';

  const initial = (site.domain || '?').replace(/^www\./, '').charAt(0).toUpperCase();

  const showAnalyzeSection = site.status === 'crawled' || site.status === 'analyzed' || site.status === 'analyzing';

  return (
    <div
      className="bg-white rounded-2xl mb-5 overflow-hidden transition-all duration-200 hover:-translate-y-px"
      style={{
        boxShadow: '0 4px 24px rgba(0,0,0,0.06), 0 1px 4px rgba(0,0,0,0.04)',
        border: '1px solid #eef0f4',
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLElement).style.boxShadow =
          '0 8px 32px rgba(0,0,0,0.10), 0 2px 8px rgba(0,0,0,0.06)';
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.boxShadow =
          '0 4px 24px rgba(0,0,0,0.06), 0 1px 4px rgba(0,0,0,0.04)';
      }}
    >
      {/* Card Top */}
      <div
        className="px-7 pt-6 pb-5"
        style={{
          borderBottom: '1px solid #f0f2f5',
          background: 'linear-gradient(135deg, #fafbff 0%, #f5f7fa 100%)',
        }}
      >
        <div className="flex items-center gap-3 flex-wrap">
          <div
            className="w-11 h-11 rounded-xl flex items-center justify-center text-xl font-bold text-white flex-shrink-0 uppercase"
            style={{ background: 'linear-gradient(135deg, #4a6cf7, #7c3aed)' }}
          >
            {initial}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-[18px] font-bold tracking-tight" style={{ color: '#1a1a2e' }}>
              {site.domain}
            </div>
            <div className="text-[13px] mt-0.5 truncate" style={{ color: '#9ca3af' }}>
              {site.url}
            </div>
          </div>
          <div className="flex gap-3 items-center flex-shrink-0 flex-wrap">
            <StatusBadge status={site.status} />
            {site.page_count > 0 && (
              <span
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-[12px] font-semibold"
                style={{ background: '#f0f4ff', color: '#4a6cf7' }}
              >
                <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                {site.page_count} pages
              </span>
            )}
            <button
              onClick={() => void onRemove(site.domain)}
              className="p-1.5 rounded-lg transition-colors hover:bg-red-50"
              style={{ color: '#dc3545' }}
              title="Remove site"
            >
              <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Card Body */}
      <div className="px-7 py-5 pb-6">
        <CrawlSection
          site={site}
          crawlJobData={crawlJobData}
          crawlPct={crawlPct}
          crawlMessage={crawlMessage}
          crawlError={crawlError}
          onStartCrawl={handleStartCrawl}
        />
        {showAnalyzeSection && (
          <AnalyzeSection
            site={site}
            analyzePct={analyzePct}
            analyzeMessage={analyzeMessage}
            analyzeError={analyzeError}
            latestAnalysisReport={latestAnalysisReport}
            onStartAnalyze={handleStartAnalyze}
          />
        )}
        <AnalysisHistory analyses={siteAnalyses} onDeleteAnalysis={handleDeleteAnalysis} />
      </div>
    </div>
  );
}
