import { useQuery } from '@tanstack/react-query';
import { api } from '@services/api';

export function useSites() {
  return useQuery({
    queryKey: ['sites'],
    queryFn: api.getSites,
    staleTime: 1000 * 30,
  });
}
