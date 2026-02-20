import { createFileRoute } from '@tanstack/react-router';
import { ReportsTab } from '@components/reports/ReportsTab';

export const Route = createFileRoute('/reports')({
  component: ReportsTab,
});
