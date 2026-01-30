import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { usePRCommentStats } from '../hooks/use-pr-comment-stats';
import { StatsKPI } from './pr-stats/stats-kpi';
import { CategoryDistribution } from './pr-stats/category-distribution';
import { SeverityDistribution } from './pr-stats/severity-distribution';
import { LoadingSkeleton } from './pr-stats/loading-skeleton';
import { EmptyState } from './pr-stats/empty-state';
import { ErrorState } from './pr-stats/error-state';

interface PRCommentStatsWidgetProps {
  username: string;
}

export function PRCommentStatsWidget({ username }: PRCommentStatsWidgetProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const { data, isLoading, error } = usePRCommentStats(username);

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (error) {
    return <ErrorState error={error as Error} />;
  }

  if (!data || data.rates.total_comments === 0) {
    return <EmptyState />;
  }

  const hasCharts = data.categories.length > 0 || data.severities.some(s => s.count > 0);

  return (
    <div className="bg-card rounded-lg border border-border p-6 space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4 text-foreground">PR Comment Analysis</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <StatsKPI
            label="Actionable Comments"
            value={data.rates.actionable_rate}
            icon="target"
            color="primary"
          />
          <StatsKPI
            label="Nitpick Rate"
            value={data.rates.nitpick_rate}
            icon="search"
            color="warning"
          />
        </div>
        <div className="mt-4 text-sm text-muted-foreground">
          Total Comments: {data.rates.total_comments}
        </div>

        {/* See More / See Less Button */}
        {hasCharts && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="mt-4 flex items-center gap-2 text-sm text-primary hover:text-primary/80 transition-colors"
          >
            {isExpanded ? (
              <>
                <span>See Less</span>
                <ChevronUp className="h-4 w-4" />
              </>
            ) : (
              <>
                <span>See More</span>
                <ChevronDown className="h-4 w-4" />
              </>
            )}
          </button>
        )}
      </div>

      {/* Collapsible Charts Section */}
      {isExpanded && hasCharts && (
        <>
          {/* Category Distribution */}
          {data.categories.length > 0 && (
            <div className="pt-6 border-t border-border">
              <h4 className="text-md font-semibold mb-3 text-foreground">Category Distribution</h4>
              <CategoryDistribution data={data.categories} />
            </div>
          )}

          {/* Severity Distribution */}
          {data.severities.some(s => s.count > 0) && (
            <div className="pt-6 border-t border-border">
              <h4 className="text-md font-semibold mb-3 text-foreground">Severity Distribution</h4>
              <SeverityDistribution data={data.severities} />
            </div>
          )}
        </>
      )}
    </div>
  );
}
