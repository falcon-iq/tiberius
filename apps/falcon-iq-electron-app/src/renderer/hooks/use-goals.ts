import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { AddGoalInput } from '@generatedtypes/electron';

const GOALS_QUERY_KEY = ['goals'];

/**
 * Hook to fetch all goals from SQLite database
 */
export function useGoals() {
  return useQuery({
    queryKey: GOALS_QUERY_KEY,
    queryFn: async () => {
      const result = await window.api.getGoals();
      if (!result.success) {
        throw new Error(result.error || 'Failed to fetch goals');
      }
      return result.data || [];
    },
  });
}

/**
 * Hook to add a new goal to the database
 */
export function useAddGoal() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (goal: AddGoalInput) => {
      const result = await window.api.addGoal(goal);
      if (!result.success) {
        throw new Error(result.error || 'Failed to add goal');
      }
      return result.data;
    },
    onSuccess: () => {
      // Invalidate and refetch goals query
      void queryClient.invalidateQueries({ queryKey: GOALS_QUERY_KEY });
    },
  });
}

/**
 * Hook to delete a goal from the database
 */
export function useDeleteGoal() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      const result = await window.api.deleteGoal(id);
      if (!result.success) {
        throw new Error(result.error || 'Failed to delete goal');
      }
    },
    onSuccess: () => {
      // Invalidate and refetch goals query
      void queryClient.invalidateQueries({ queryKey: GOALS_QUERY_KEY });
    },
  });
}

/**
 * Hook to update a goal (typically to set end_date)
 */
export function useUpdateGoal() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (goal: { id: number; end_date?: string | null }) => {
      const result = await window.api.updateGoal(goal);
      if (!result.success) {
        throw new Error(result.error || 'Failed to update goal');
      }
    },
    onSuccess: () => {
      // Invalidate and refetch goals query
      void queryClient.invalidateQueries({ queryKey: GOALS_QUERY_KEY });
    },
  });
}
