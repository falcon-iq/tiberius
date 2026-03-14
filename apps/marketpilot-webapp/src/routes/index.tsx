import { createFileRoute } from '@tanstack/react-router';
import { BenchmarkPage } from '@components/BenchmarkPage';
import { ComingSoonTab } from '@components/ComingSoonTab';
import { TabNavigation, type Tab } from '@components/TabNavigation';

export const Route = createFileRoute('/')({
  component: HomePage,
});

/* ── SVG icon helpers ─────────────────────────────────────────── */

const iconProps = { viewBox: '0 0 24 24', fill: 'none', strokeWidth: '2', strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const, style: { width: 16, height: 16 } };

const PlanIcon = () => (
  <svg {...iconProps} stroke="#818cf8">
    <circle cx="12" cy="12" r="10" />
    <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
  </svg>
);

const ExperimentIcon = () => (
  <svg {...iconProps} stroke="#f59e0b">
    <path d="M9 3h6M12 3v7l4 8H8l4-8V3z" />
  </svg>
);

const ExecuteIcon = () => (
  <svg {...iconProps} stroke="#10b981">
    <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
  </svg>
);

const MeasureIcon = () => (
  <svg {...iconProps} stroke="#f472b6">
    <path d="M18 20V10M12 20V4M6 20v-6" />
  </svg>
);

/* ── Feature icon helpers (for coming soon cards) ─────────────── */

const featureIconStyle = { width: 20, height: 20 };
const featureIconProps = { viewBox: '0 0 24 24', fill: 'none', strokeWidth: '2', strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const, style: featureIconStyle };

/* ── Tab definitions ─────────────────────────────────────────── */

const tabs: Tab[] = [
  {
    id: 'plan',
    label: 'Plan',
    icon: <PlanIcon />,
    content: <BenchmarkPage />,
  },
  {
    id: 'experiment',
    label: 'Experiment',
    icon: <ExperimentIcon />,
    content: (
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
    ),
  },
  {
    id: 'execute',
    label: 'Execute',
    icon: <ExecuteIcon />,
    content: (
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
    ),
  },
  {
    id: 'measure',
    label: 'Measure',
    icon: <MeasureIcon />,
    content: (
      <ComingSoonTab
        title="Measure Real Business Impact"
        subtitle="Connect LLM exposure to traffic, leads, and pipeline"
        description="Visibility without measurement is just vanity. Market Presence's measurement layer connects the dots between your LLM presence and real business outcomes. Through advanced attribution modeling, track how AI-driven brand mentions translate into website visits, qualified leads, and actual pipeline growth. Prove ROI on your LLM marketing strategy with data, not guesswork."
        accentColor="#f472b6"
        accentColorRgb="244, 114, 182"
        features={[
          {
            icon: <svg {...featureIconProps} stroke="#f472b6"><path d="M18 20V10M12 20V4M6 20v-6" /></svg>,
            title: 'Attribution Modeling',
            description: 'Multi-touch attribution that traces customer journeys from LLM discovery through conversion and revenue.',
          },
          {
            icon: <svg {...featureIconProps} stroke="#f472b6"><path d="M22 12h-4l-3 9L9 3l-3 9H2" /></svg>,
            title: 'Lift Analysis',
            description: 'Measure the incremental impact of LLM visibility on traffic, engagement, and demand generation metrics.',
          },
          {
            icon: <svg {...featureIconProps} stroke="#f472b6"><circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" /></svg>,
            title: 'Real-Time Dashboards',
            description: 'Live dashboards connecting LLM brand sentiment to pipeline metrics, updated as AI models evolve.',
          },
        ]}
      />
    ),
  },
];

function HomePage() {
  return <TabNavigation tabs={tabs} defaultTab="plan" />;
}
