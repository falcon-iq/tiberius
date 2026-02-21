import { useQuery } from '@tanstack/react-query';
import type { CrawlJobStatus } from '@app-types/api';
import { api } from '@services/api';

export function useCrawlJob(jobId: string | null) {
  return useQuery<CrawlJobStatus>({
    queryKey: ['crawl-job', jobId],
    queryFn: () => api.getCrawlJob(jobId!),
    enabled: !!jobId,
    staleTime: 0,
    refetchInterval: (query) => {
      const status = (query.state.data as CrawlJobStatus | undefined)?.status;
      return status === 'completed' || status === 'failed' ? false : 2000;
    },
  });
}
