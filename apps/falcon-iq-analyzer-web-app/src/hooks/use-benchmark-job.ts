import { useQuery } from '@tanstack/react-query';
import type { BenchmarkJobStatus } from '@app-types/api';
import { api } from '@services/api';

export function useBenchmarkJob(jobId: string | null) {
  return useQuery<BenchmarkJobStatus>({
    queryKey: ['benchmark-job', jobId],
    queryFn: () => api.getBenchmarkJob(jobId!),
    enabled: !!jobId,
    staleTime: 0,
    refetchInterval: (query) => {
      const status = (query.state.data as BenchmarkJobStatus | undefined)?.status;
      return status === 'completed' || status === 'failed' ? false : 3000;
    },
  });
}
