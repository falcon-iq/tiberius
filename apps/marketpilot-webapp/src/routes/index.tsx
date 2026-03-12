import { createFileRoute } from '@tanstack/react-router';
import { BenchmarkPage } from '@components/BenchmarkPage';

export const Route = createFileRoute('/')({
  component: BenchmarkPage,
});
