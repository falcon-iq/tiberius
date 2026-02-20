import { useState } from 'react';
import type { BenchmarkResult } from '@app-types/api';
import { useAnalyses } from '@hooks/use-analyses';
import { useBenchmarks } from '@hooks/use-benchmarks';
import { api } from '@services/api';
import { BenchmarkDashboard } from '@components/benchmark/BenchmarkDashboard';
import { MarkdownRenderer } from '@components/shared/MarkdownRenderer';

type ReportType = 'benchmark' | 'analysis';

interface AnalysisReport {
  jobId: string;
  markdown: string;
  companyName: string;
}

export function ReportsTab() {
  const [reportType, setReportType] = useState<ReportType>('benchmark');
  const [selectedJobId, setSelectedJobId] = useState('');
  const [currentBenchmarkReport, setCurrentBenchmarkReport] = useState<BenchmarkResult | null>(null);
  const [currentAnalysisReport, setCurrentAnalysisReport] = useState<AnalysisReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  const { data: analyses = [] } = useAnalyses();
  const { data: benchmarks = [] } = useBenchmarks();

  const clearReport = () => {
    setCurrentBenchmarkReport(null);
    setCurrentAnalysisReport(null);
    setLoadError(null);
  };

  const handleReportTypeChange = (type: ReportType) => {
    setReportType(type);
    setSelectedJobId('');
    clearReport();
  };

  const handleReportSelected = async (jobId: string) => {
    setSelectedJobId(jobId);
    if (!jobId) {
      clearReport();
      return;
    }

    setIsLoading(true);
    setLoadError(null);
    try {
      if (reportType === 'benchmark') {
        const data = await api.getBenchmarkJob(jobId);
        if (data.status === 'completed' && data.result) {
          setCurrentBenchmarkReport(data.result);
          setCurrentAnalysisReport(null);
        } else {
          setLoadError('Report not available.');
        }
      } else {
        const data = await api.getAnalyzeJob(jobId);
        if (data.status === 'completed' && data.result?.markdown_report) {
          setCurrentAnalysisReport({
            jobId,
            markdown: data.result.markdown_report,
            companyName: data.result.company_name,
          });
          setCurrentBenchmarkReport(null);
        } else {
          setLoadError('Report not available.');
        }
      }
    } catch (e) {
      setLoadError('Failed to load report: ' + (e as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = () => {
    let md = '';
    let filename = 'report.md';

    if (currentBenchmarkReport?.markdown_report) {
      md = currentBenchmarkReport.markdown_report;
      filename = 'benchmark-report.md';
    } else if (currentAnalysisReport) {
      md = currentAnalysisReport.markdown;
      filename = `${currentAnalysisReport.companyName || 'analysis'}-report.md`;
    }

    if (!md) {
      alert('No markdown report available');
      return;
    }

    const blob = new Blob([md], { type: 'text/markdown' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const hasReport = !!(currentBenchmarkReport || currentAnalysisReport);

  return (
    <div>
      <div
        className="bg-white rounded-2xl overflow-hidden mb-5"
        style={{
          boxShadow: '0 4px 24px rgba(0,0,0,0.06), 0 1px 4px rgba(0,0,0,0.04)',
          border: '1px solid #eef0f4',
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
          <div className="flex items-center gap-3">
            <div
              className="w-11 h-11 rounded-xl flex items-center justify-center text-white"
              style={{ background: 'linear-gradient(135deg, #28a745, #20c997)' }}
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
              </svg>
            </div>
            <div>
              <div className="text-[18px] font-bold" style={{ color: '#1a1a2e' }}>
                Reports
              </div>
              <div className="text-[13px]" style={{ color: '#9ca3af' }}>
                View and download benchmark and analysis reports
              </div>
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="px-7 py-5">
          <div className="flex gap-3 items-end flex-wrap">
            <div className="flex-1 min-w-[160px]">
              <label className="block text-[13px] font-semibold mb-1" style={{ color: '#555' }}>
                Report type
              </label>
              <select
                value={reportType}
                onChange={(e) => handleReportTypeChange(e.target.value as ReportType)}
                className="w-full px-3 py-2.5 rounded-lg text-[14px] focus:outline-none"
                style={{ border: '1px solid #ddd' }}
              >
                <option value="benchmark">Benchmark Reports</option>
                <option value="analysis">Analysis Reports</option>
              </select>
            </div>
            <div className="flex-1 min-w-[160px]">
              <label className="block text-[13px] font-semibold mb-1" style={{ color: '#555' }}>
                Select report
              </label>
              <select
                value={selectedJobId}
                onChange={(e) => void handleReportSelected(e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg text-[14px] focus:outline-none"
                style={{ border: '1px solid #ddd' }}
              >
                <option value="">-- Select a report --</option>
                {reportType === 'benchmark'
                  ? benchmarks.map((b) => (
                      <option key={b.job_id} value={b.job_id}>
                        {b.company_a} vs {b.company_b} ({b.total_prompts} prompts)
                      </option>
                    ))
                  : analyses.map((a) => (
                      <option key={a.job_id} value={a.job_id}>
                        {a.company_name} ({a.job_id})
                      </option>
                    ))}
              </select>
            </div>
            <div>
              <button
                onClick={handleDownload}
                disabled={!hasReport}
                className="flex items-center gap-1.5 px-5 py-2.5 text-white rounded-lg text-[12px] font-semibold transition-colors disabled:cursor-not-allowed"
                style={{ background: hasReport ? '#28a745' : '#b0b8d1' }}
                onMouseEnter={(e) => {
                  if (hasReport) (e.currentTarget as HTMLElement).style.background = '#218838';
                }}
                onMouseLeave={(e) => {
                  if (hasReport) (e.currentTarget as HTMLElement).style.background = '#28a745';
                }}
              >
                <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                  <polyline points="7 10 12 15 17 10" />
                  <line x1="12" y1="15" x2="12" y2="3" />
                </svg>
                Download
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Report Display */}
      {isLoading && (
        <div className="text-center py-6 flex items-center justify-center gap-2" style={{ color: '#9ca3af' }}>
          <span className="spinner-icon" />
          Loading report...
        </div>
      )}

      {loadError && !isLoading && (
        <div className="text-center py-6" style={{ color: '#dc3545' }}>
          {loadError}
        </div>
      )}

      {currentBenchmarkReport && !isLoading && (
        currentBenchmarkReport.summary ? (
          <BenchmarkDashboard result={currentBenchmarkReport} />
        ) : currentBenchmarkReport.markdown_report ? (
          <div className="bg-white rounded-xl shadow-sm p-6">
            <MarkdownRenderer content={currentBenchmarkReport.markdown_report} />
          </div>
        ) : null
      )}

      {currentAnalysisReport && !isLoading && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <MarkdownRenderer content={currentAnalysisReport.markdown} />
        </div>
      )}
    </div>
  );
}
