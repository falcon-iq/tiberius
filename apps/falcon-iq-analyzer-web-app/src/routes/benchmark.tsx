import { createFileRoute } from '@tanstack/react-router';
import { BenchmarkTab } from '@components/benchmark/BenchmarkTab';

export const Route = createFileRoute('/benchmark')({
  component: BenchmarkTab,
});
