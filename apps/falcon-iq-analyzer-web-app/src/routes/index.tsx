import { createFileRoute } from '@tanstack/react-router';
import { WebsitesTab } from '@components/websites/WebsitesTab';

export const Route = createFileRoute('/')({
  component: WebsitesTab,
});
