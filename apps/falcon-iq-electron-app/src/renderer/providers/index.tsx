import { ThemeProvider } from '@libs/shared/hooks/use-theme';
import { QueryProvider } from './QueryProvider';

interface AppProvidersProps {
  children: React.ReactNode;
}

/**
 * AppProviders composes all application-level providers
 * Add new providers here as needed (Auth, WebSocket, ErrorBoundary, etc.)
 */
export const AppProviders = ({ children }: AppProvidersProps) => {
  return (
    <QueryProvider>
      <ThemeProvider defaultTheme="light" storageKey="theme">
        {children}
      </ThemeProvider>
    </QueryProvider>
  );
};

// Re-export individual providers and utilities for direct use if needed
export { QueryProvider } from './QueryProvider';
export { queryClient } from './queryClient';
