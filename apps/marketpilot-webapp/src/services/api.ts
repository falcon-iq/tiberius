import type { StartBenchmarkRequest, StartBenchmarkResponse, BenchmarkStatusResponse } from '@app-types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, options);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(
      (data as { error?: string }).error ?? `Request failed: ${res.status}`,
    );
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}

export const api = {
  startBenchmark: (req: StartBenchmarkRequest) =>
    request<StartBenchmarkResponse>('/api/company-benchmark-report/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        userId: 'market-pilot-web',
        companyLink: req.companyUrl,
        otherCompanyLinks: req.competitorUrls,
      }),
    }),

  getBenchmarkStatus: (id: string) =>
    request<BenchmarkStatusResponse>(`/api/company-benchmark-report/${id}`),
};
