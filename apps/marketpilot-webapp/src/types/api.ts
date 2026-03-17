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

export interface CompanyStrength {
  title: string;
  detail: string;
}

export interface CompanyImprovement {
  title: string;
  detail: string;
}

export interface CompanyTestimonial {
  quote: string;
  source: string;
  authorRole: string;
}

export interface CompanyKeyFact {
  label: string;
  value: string;
  source: string;
  sourceUrl: string;
}

export interface IndustryCompanyEntry {
  companyName: string;
  companyUrl: string;
  logoUrl?: string;
  keyFacts: CompanyKeyFact[];
  strengths: CompanyStrength[];
  improvements: CompanyImprovement[];
  testimonials: CompanyTestimonial[];
}

export interface IndustryBenchmarkSummary {
  id: string;
  industryName: string;
  country: string;
  slug: string;
  generatedAt: number;
  companyCount: number;
}

export interface IndustryBenchmarkDetail extends IndustryBenchmarkSummary {
  companies: IndustryCompanyEntry[];
}
