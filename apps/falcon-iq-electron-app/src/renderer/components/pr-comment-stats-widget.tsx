import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { usePRCommentStats } from '../hooks/use-pr-comment-stats';
import { CategoryDistribution } from './pr-stats/category-distribution';
import { SeverityDistribution } from './pr-stats/severity-distribution';
import { LoadingSkeleton } from './pr-stats/loading-skeleton';
import { EmptyState } from './pr-stats/empty-state';
import { ErrorState } from './pr-stats/error-state';
import { CommentDetailsModal } from './comment-details-modal';
import type { MetricType } from '../types/electron';

interface PRCommentStatsWidgetProps {
  username: string;
}

interface MetricCardConfig {
  id: MetricType;
  emoji: string;
  title: string;
  description: string;
  bgColor: string;
  getValue: (data: any) => number;
}

const METRICS: MetricCardConfig[] = [
  {
    id: 'bugs_in_logic',
    emoji: '🐛',
    title: 'Bugs in Business Logic',
    description: 'Critical correctness issues',
    bgColor: 'bg-red-500/10 dark:bg-red-500/20',
    getValue: (data) => data.metrics.bugs_in_logic,
  },
  {
    id: 'design_thinking',
    emoji: '🏛️',
    title: 'Design Thinking',
    description: 'Architecture and design feedback',
    bgColor: 'bg-purple-500/10 dark:bg-purple-500/20',
    getValue: (data) => data.metrics.design_thinking,
  },
  {
    id: 'balanced_feedback',
    emoji: '👏',
    title: 'Balanced Feedback',
    description: 'Praise and acknowledgment',
    bgColor: 'bg-green-500/10 dark:bg-green-500/20',
    getValue: (data) => data.metrics.balanced_feedback,
  },
  {
    id: 'high_engagement',
    emoji: '💬',
    title: 'High Engagement',
    description: 'Questions and clarification',
    bgColor: 'bg-blue-500/10 dark:bg-blue-500/20',
    getValue: (data) => data.metrics.high_engagement,
  },
  {
    id: 'nitpick_rate',
    emoji: '📝',
    title: 'Nitpick Rate',
    description: 'Minor style and formatting',
    bgColor: 'bg-gray-500/10 dark:bg-gray-500/20',
    getValue: (data) => data.metrics.nitpick_rate,
  },
];

const SYSTEM_SUB_METRICS: MetricCardConfig[] = [
  {
    id: 'edge_cases',
    emoji: '🔍',
    title: 'Edge Cases',
    description: '',
    bgColor: '',
    getValue: (data) => data.metrics.system_level_concerns.edge_cases,
  },
  {
    id: 'reliability',
    emoji: '🛡️',
    title: 'Reliability',
    description: '',
    bgColor: '',
    getValue: (data) => data.metrics.system_level_concerns.reliability,
  },
  {
    id: 'performance',
    emoji: '⚡',
    title: 'Performance',
    description: '',
    bgColor: '',
    getValue: (data) => data.metrics.system_level_concerns.performance,
  },
  {
    id: 'bug_correctness',
    emoji: '🐛',
    title: 'Bug/Correctness',
    description: '',
    bgColor: '',
    getValue: (data) => data.metrics.system_level_concerns.bug_correctness,
  },
];

export function PRCommentStatsWidget({ username }: PRCommentStatsWidgetProps) {
  const [isLegacyExpanded, setIsLegacyExpanded] = useState(false);
  const [systemExpanded, setSystemExpanded] = useState(false);
  const [modalState, setModalState] = useState<{
    isOpen: boolean;
    metricType: MetricType | null;
    metricName: string;
  }>({
    isOpen: false,
    metricType: null,
    metricName: '',
  });

  const { data, isLoading, error } = usePRCommentStats(username);

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (error) {
    return <ErrorState error={error as Error} />;
  }

  if (!data || data.summary.total_comments === 0) {
    return <EmptyState />;
  }

  const handleMetricClick = (metricType: MetricType, metricName: string) => {
    setModalState({
      isOpen: true,
      metricType,
      metricName,
    });
  };

  const closeModal = () => {
    setModalState({
      isOpen: false,
      metricType: null,
      metricName: '',
    });
  };

  const hasCharts = data.categories && data.categories.length > 0 ||
                    data.severities && data.severities.some(s => s.count > 0);

  return (
    <>
      <div className="bg-card rounded-lg border border-border p-6">
        {/* Header Section */}
        <div className="mb-6">
          <h3 className="text-xl font-bold text-foreground mb-2">
            Key Review Metrics
          </h3>
          <p className="text-sm text-muted-foreground">
            {data.summary.total_comments} comments across {data.summary.pr_count} PRs, {data.summary.author_count} authors
          </p>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {METRICS.map((metric) => (
            <button
              key={metric.id}
              onClick={() => handleMetricClick(metric.id, metric.title)}
              className="group relative flex items-center gap-4 p-5 bg-card border border-border rounded-lg hover:shadow-md hover:border-primary/50 transition-all cursor-pointer text-left"
            >
              <div className={`flex-shrink-0 w-12 h-12 rounded-full ${metric.bgColor} flex items-center justify-center text-2xl`}>
                {metric.emoji}
              </div>
              <div className="flex-1 min-w-0">
                <h4 className="font-semibold text-foreground mb-1">
                  {metric.title}
                </h4>
                <p className="text-sm text-muted-foreground">
                  {metric.description}
                </p>
              </div>
              <div className="flex-shrink-0 text-right">
                <div className="text-2xl font-bold text-foreground">
                  {metric.getValue(data).toFixed(1)}%
                </div>
                <div className="text-xs text-muted-foreground">
                  Click to view
                </div>
              </div>
            </button>
          ))}

          {/* System-Level Concerns Card (Expandable) */}
          <div className="md:col-span-2">
            <div className="border border-border rounded-lg overflow-hidden">
              <button
                onClick={() => setSystemExpanded(!systemExpanded)}
                className="w-full flex items-center gap-4 p-5 bg-card hover:bg-muted/50 transition-colors text-left"
              >
                <div className="flex-shrink-0 w-12 h-12 rounded-full bg-blue-500/10 dark:bg-blue-500/20 flex items-center justify-center text-2xl">
                  ⚙️
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold text-foreground mb-1">System-Level Concerns</h4>
                  <p className="text-sm text-muted-foreground">Reliability, performance, edge cases</p>
                </div>
                <div className="text-2xl font-bold text-foreground">
                  {data.metrics.system_level_concerns.total.toFixed(1)}%
                </div>
                {systemExpanded ? (
                  <ChevronUp className="w-5 h-5 text-muted-foreground transition-transform" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-muted-foreground transition-transform" />
                )}
              </button>

              {systemExpanded && (
                <div className="border-t border-border bg-muted/20 p-4 space-y-2">
                  {SYSTEM_SUB_METRICS.map((subMetric) => (
                    <button
                      key={subMetric.id}
                      onClick={() => handleMetricClick(subMetric.id, subMetric.title)}
                      className="w-full flex items-center justify-between p-3 rounded hover:bg-background transition-colors text-left group"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{subMetric.emoji}</span>
                        <span className="text-sm font-medium text-foreground">{subMetric.title}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-semibold text-foreground">
                          {subMetric.getValue(data).toFixed(1)}%
                        </span>
                        <span className="text-xs text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">
                          View
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Optional: Legacy Charts */}
        {hasCharts && (
          <button
            onClick={() => setIsLegacyExpanded(!isLegacyExpanded)}
            className="mt-6 flex items-center gap-2 text-sm text-primary hover:text-primary/80 transition-colors"
          >
            {isLegacyExpanded ? (
              <>
                <span>Hide Detailed Breakdown</span>
                <ChevronUp className="h-4 w-4" />
              </>
            ) : (
              <>
                <span>View Detailed Breakdown</span>
                <ChevronDown className="h-4 w-4" />
              </>
            )}
          </button>
        )}

        {/* Collapsible legacy charts */}
        {isLegacyExpanded && hasCharts && (
          <>
            {data.categories && data.categories.length > 0 && (
              <div className="pt-6 border-t border-border">
                <h4 className="text-md font-semibold mb-3 text-foreground">
                  Category Distribution
                </h4>
                <CategoryDistribution data={data.categories} />
              </div>
            )}

            {data.severities && data.severities.some(s => s.count > 0) && (
              <div className="pt-6 border-t border-border">
                <h4 className="text-md font-semibold mb-3 text-foreground">
                  Severity Distribution
                </h4>
                <SeverityDistribution data={data.severities} />
              </div>
            )}
          </>
        )}
      </div>

      {/* Modal for comment details */}
      {modalState.metricType && (
        <CommentDetailsModal
          isOpen={modalState.isOpen}
          onClose={closeModal}
          username={username}
          metricType={modalState.metricType}
          metricName={modalState.metricName}
        />
      )}
    </>
  );
}
