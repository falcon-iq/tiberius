import { createFileRoute } from '@tanstack/react-router';
import { IndustryBenchmarksTab } from '@components/IndustryBenchmarksTab';

export const Route = createFileRoute('/industries')({
  component: IndustryBenchmarksTab,
});
