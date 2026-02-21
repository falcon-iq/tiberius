export type SiteStatus = 'pending' | 'crawling' | 'crawled' | 'analyzing' | 'analyzed' | 'failed';

export interface Site {
  domain: string;
  directory: string;
  page_count: number;
}

export interface LocalSite {
  url: string;
  domain: string;
  directory: string | null;
  page_count: number;
  status: SiteStatus;
  maxPages: number;
}

export interface CrawlJobStatus {
  job_id: string;
  status: 'running' | 'completed' | 'failed';
  page_count: number;
  output_dir: string;
  progress: string;
  error?: string;
}

export interface AnalysisResult {
  markdown_report: string;
  company_name: string;
  total_pages?: number;
  product_pages_analyzed?: number;
}

export interface AnalyzeJobStatus {
  job_id: string;
  status: 'running' | 'completed' | 'failed';
  progress: string;
  result?: AnalysisResult;
  error?: string;
}

export interface Analysis {
  job_id: string;
  company_name: string;
  domain?: string;
  crawl_directory?: string;
  total_pages?: number;
  product_pages_analyzed?: number;
  created_at?: string;
}

export interface CompanyMention {
  sentiment: number;
  strengths_mentioned?: string[];
  weaknesses_mentioned?: string[];
}

export interface BenchmarkEvaluation {
  category?: string;
  winner?: 'company_a' | 'company_b' | 'tie';
  prompt_text?: string;
  company_a_mention?: CompanyMention;
  company_b_mention?: CompanyMention;
  analysis_notes?: string;
  llm_response?: string;
}

export interface BenchmarkSummary {
  company_a: string;
  company_b: string;
  total_prompts: number;
  company_a_wins: number;
  company_b_wins: number;
  ties: number;
  company_a_avg_sentiment: number;
  company_b_avg_sentiment: number;
  company_a_top_strengths?: string[];
  company_a_top_weaknesses?: string[];
  company_b_top_strengths?: string[];
  company_b_top_weaknesses?: string[];
  key_insights?: string[];
}

export interface BenchmarkResult {
  summary?: BenchmarkSummary;
  evaluations?: BenchmarkEvaluation[];
  markdown_report?: string;
}

export interface BenchmarkJobStatus {
  job_id: string;
  status: 'running' | 'completed' | 'failed';
  progress: string;
  result?: BenchmarkResult;
  error?: string;
}

export interface Benchmark {
  job_id: string;
  company_a: string;
  company_b: string;
  company_a_wins?: number;
  company_b_wins?: number;
  total_prompts: number;
  created_at?: string;
}
