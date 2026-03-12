export type BenchmarkStatus =
  | 'NOT_STARTED'
  | 'CRAWL_IN_PROGRESS'
  | 'CRAWL_COMPLETED'
  | 'ANALYSIS_IN_PROGRESS'
  | 'ANALYSIS_COMPLETED'
  | 'BENCHMARK_REPORT_IN_PROGRESS'
  | 'COMPLETED'
  | 'FAILED';

export interface StartBenchmarkRequest {
  companyUrl: string;
  competitorUrls: string[];
}

export interface StartBenchmarkResponse {
  id: string;
}

export interface BenchmarkStatusResponse {
  id: string;
  status: BenchmarkStatus;
  progress?: number;
  analyzerBaseUrl?: string;
  reportId?: string;
  htmlReportUrl?: string;
  errorMessage?: string;
}
