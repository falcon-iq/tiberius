import { useQuery } from '@tanstack/react-query';

/**
 * Hook to fetch PR comment statistics for a user
 */
export function usePRCommentStats(username: string) {
  return useQuery({
    queryKey: ['pr-comment-stats', username],
    queryFn: async () => {
      const result = await window.api.getPRCommentStats(username);
      if (!result.success) {
        console.log("---------------------------------->", result.error);
        throw new Error(result.error || 'Failed to fetch PR comment stats');
      }
      return result.data || null;
    },
    enabled: !!username,
  });
}
