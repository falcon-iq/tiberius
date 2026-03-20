import { createFileRoute } from '@tanstack/react-router';
import { ComingSoonTab } from '@components/ComingSoonTab';

const featureIconStyle = { width: 20, height: 20 };
const featureIconProps = { viewBox: '0 0 24 24', fill: 'none', strokeWidth: '2', strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const, style: featureIconStyle };

function ExperimentPage() {
  return (
    <ComingSoonTab
      title="Experiment & Optimize"
      subtitle="Run controlled tests to improve how LLMs recommend your brand"
      description="Marketing in the age of AI requires a new kind of experimentation. Market Presence lets you run A/B tests on messaging, prompts, and landing pages to see how changes affect the way large language models describe and recommend your products. Test different value propositions, content structures, and Q&A approaches to find what resonates with AI-driven discovery."
      accentColor="#f59e0b"
      accentColorRgb="245, 158, 11"
      features={[
        {
          icon: <svg {...featureIconProps} stroke="#f59e0b"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="8.5" cy="7" r="4" /><path d="M20 8v6M23 11h-6" /></svg>,
          title: 'A/B Test Messaging',
          description: 'Compare how different copy, value props, and positioning affect LLM recommendations for your brand.',
        },
        {
          icon: <svg {...featureIconProps} stroke="#f59e0b"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" /></svg>,
          title: 'Prompt Variation Testing',
          description: 'See how different user queries and prompts change the way AI surfaces your product versus competitors.',
        },
        {
          icon: <svg {...featureIconProps} stroke="#f59e0b"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" /></svg>,
          title: 'Landing Page Optimization',
          description: 'Test landing page variants to discover which structures and content formats AI models prefer to cite.',
        },
      ]}
    />
  );
}

export const Route = createFileRoute('/experiment')({
  component: ExperimentPage,
});
