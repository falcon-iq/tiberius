import { useQuery } from '@tanstack/react-query';
import { api } from '@services/api';

export function useBenchmarks() {
  return useQuery({
    queryKey: ['benchmarks'],
    queryFn: api.getBenchmarks,
    staleTime: 1000 * 30,
  });
}
