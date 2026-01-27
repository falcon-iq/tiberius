import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { AppSettings } from '@generatedtypes/electron';

const SETTINGS_QUERY_KEY = ['settings'];

/**
 * Hook to fetch app settings from settings.json
 */
export function useSettings() {
  return useQuery({
    queryKey: SETTINGS_QUERY_KEY,
    queryFn: async () => {
      const result = await window.api.settings.get();
      if (!result.success) {
        throw new Error(result.error || 'Failed to fetch settings');
      }
      return result.data;
    },
  });
}

/**
 * Hook to save complete settings object
 */
export function useSaveSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (settings: AppSettings) => {
      const result = await window.api.settings.save(settings);
      if (!result.success) {
        throw new Error(result.error || 'Failed to save settings');
      }
    },
    onSuccess: () => {
      // Invalidate and refetch settings query
      void queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEY });
    },
  });
}

/**
 * Hook to update partial settings (merges with existing)
 */
export function useUpdateSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (partial: Partial<AppSettings>) => {
      const result = await window.api.settings.update(partial);
      if (!result.success) {
        throw new Error(result.error || 'Failed to update settings');
      }
    },
    onSuccess: () => {
      // Invalidate and refetch settings query
      void queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEY });
    },
  });
}
