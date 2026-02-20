import { useQuery } from '@tanstack/react-query';
import { api } from '@services/api';

export function useAnalyses() {
  return useQuery({
    queryKey: ['analyses'],
    queryFn: api.getAnalyses,
    staleTime: 1000 * 30,
  });
}
