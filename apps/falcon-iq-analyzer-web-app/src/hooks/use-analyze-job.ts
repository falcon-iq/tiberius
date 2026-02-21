import { useQuery } from '@tanstack/react-query';
import type { AnalyzeJobStatus } from '@app-types/api';
import { api } from '@services/api';

export function useAnalyzeJob(jobId: string | null) {
  return useQuery<AnalyzeJobStatus>({
    queryKey: ['analyze-job', jobId],
    queryFn: () => api.getAnalyzeJob(jobId!),
    enabled: !!jobId,
    staleTime: 0,
    refetchInterval: (query) => {
      const status = (query.state.data as AnalyzeJobStatus | undefined)?.status;
      return status === 'completed' || status === 'failed' ? false : 3000;
    },
  });
}
