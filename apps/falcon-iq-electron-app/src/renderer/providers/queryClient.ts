import { QueryClient } from '@tanstack/react-query';

/**
 * QueryClient instance for TanStack Query
 * Configured with sensible defaults for Electron apps
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Cache data for 5 minutes before considering it stale
      staleTime: 1000 * 60 * 5,
      // Don't refetch on window focus (Electron behavior differs from web)
      refetchOnWindowFocus: false,
      // Retry failed requests once
      retry: 1,
    },
    mutations: {
      // Retry failed mutations once
      retry: 1,
    },
  },
});
