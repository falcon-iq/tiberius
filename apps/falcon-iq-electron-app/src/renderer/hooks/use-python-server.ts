import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function usePythonServerStatus() {
  return useQuery({
    queryKey: ['python-server', 'status'],
    queryFn: () => window.api.pythonServer.getStatus(),
    refetchInterval: 30000, // Poll every 30s
  });
}

export function usePythonServerRestart() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => window.api.pythonServer.restart(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['python-server', 'status'] });
    },
  });
}
