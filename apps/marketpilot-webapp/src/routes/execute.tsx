import { createFileRoute } from '@tanstack/react-router';
import { ComingSoonTab } from '@components/ComingSoonTab';

const featureIconStyle = { width: 20, height: 20 };
const featureIconProps = { viewBox: '0 0 24 24', fill: 'none', strokeWidth: '2', strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const, style: featureIconStyle };

function ExecutePage() {
  return (
    <ComingSoonTab
      title="Execute with AI Agents"
      subtitle="Dedicated agents that continuously optimize your LLM presence"
      description="Stop manually updating content and hoping for the best. Market Presence's execution layer deploys intelligent agents that work around the clock to monitor your LLM visibility, build dynamic Q&A pages that AI models love to reference, and improve creatives in real-time. These agents adapt to changes in how models retrieve and rank information, keeping you ahead of the curve."
      accentColor="#10b981"
      accentColorRgb="16, 185, 129"
      features={[
        {
          icon: <svg {...featureIconProps} stroke="#10b981"><path d="M12 2a10 10 0 1 0 10 10" /><path d="M12 2v10l7-4" /></svg>,
          title: 'Continuous Monitoring',
          description: 'Agents track how LLMs describe your brand 24/7, alerting you to shifts in positioning or sentiment.',
        },
        {
          icon: <svg {...featureIconProps} stroke="#10b981"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>,
          title: 'Dynamic Q&A Pages',
          description: 'Auto-generate and optimize FAQ and knowledge pages structured for maximum AI discoverability.',
        },
        {
          icon: <svg {...featureIconProps} stroke="#10b981"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" /></svg>,
          title: 'Creative Optimization',
          description: 'Agents dynamically improve ad copy, landing pages, and content based on real-time LLM feedback loops.',
        },
      ]}
    />
  );
}

export const Route = createFileRoute('/execute')({
  component: ExecutePage,
});
