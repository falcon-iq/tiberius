import { createFileRoute } from '@tanstack/react-router';
import { ComingSoonTab } from '@components/ComingSoonTab';

const featureIconStyle = { width: 20, height: 20 };
const featureIconProps = { viewBox: '0 0 24 24', fill: 'none', strokeWidth: '2', strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const, style: featureIconStyle };

function MeasurePage() {
  return (
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
  );
}

export const Route = createFileRoute('/measure')({
  component: MeasurePage,
});
