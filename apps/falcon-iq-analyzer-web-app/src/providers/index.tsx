import { QueryProvider } from './QueryProvider';

interface AppProvidersProps {
  children: React.ReactNode;
}

export const AppProviders = ({ children }: AppProvidersProps) => {
  return <QueryProvider>{children}</QueryProvider>;
};

export { QueryProvider } from './QueryProvider';
export { queryClient } from './queryClient';
