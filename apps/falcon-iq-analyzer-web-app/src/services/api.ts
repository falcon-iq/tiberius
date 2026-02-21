import type {
  Site,
  CrawlJobStatus,
  AnalyzeJobStatus,
  Analysis,
  BenchmarkJobStatus,
  Benchmark,
} from '@app-types/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(path, options);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(
      (data as { detail?: string }).detail ?? `Request failed: ${res.status}`,
    );
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}

export const api = {
  getSites: () => request<Site[]>('/sites'),

  deleteSite: (domain: string) =>
    request<void>(`/sites/${encodeURIComponent(domain)}`, { method: 'DELETE' }),

  startCrawl: (url: string, maxPages: number) =>
    request<{ job_id: string }>('/crawl', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, max_pages: maxPages }),
    }),

  getCrawlJob: (jobId: string) => request<CrawlJobStatus>(`/crawl/${jobId}`),

  getAnalyses: () => request<Analysis[]>('/analyses'),

  startAnalyze: (crawlDirectory: string, companyName: string, domain: string) =>
    request<{ job_id: string }>('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        crawl_directory: crawlDirectory,
        company_name: companyName,
        domain,
      }),
    }),

  getAnalyzeJob: (jobId: string) => request<AnalyzeJobStatus>(`/analyze/${jobId}`),

  deleteAnalysis: (jobId: string) =>
    request<void>(`/analyses/${encodeURIComponent(jobId)}`, { method: 'DELETE' }),

  getBenchmarks: () => request<Benchmark[]>('/benchmarks'),

  startBenchmark: (jobIdA: string, jobIdB: string, numPrompts: number) =>
    request<{ job_id: string }>('/benchmark', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_id_a: jobIdA, job_id_b: jobIdB, num_prompts: numPrompts }),
    }),

  getBenchmarkJob: (jobId: string) => request<BenchmarkJobStatus>(`/benchmark/${jobId}`),

  deleteBenchmark: (jobId: string) =>
    request<void>(`/benchmarks/${encodeURIComponent(jobId)}`, { method: 'DELETE' }),
};
