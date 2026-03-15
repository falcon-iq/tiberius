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
  email: string;
  companyName: string;
  companyUrl: string;
  competitorUrls: string[];
}

export interface SuggestCompetitorsRequest {
  companyUrl: string;
}

export interface SuggestCompetitorsResponse {
  competitors: string[];
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
