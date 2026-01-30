export function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* KPI Cards */}
      <div className="bg-card rounded-lg border border-border p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="h-32 bg-muted rounded-lg"></div>
          <div className="h-32 bg-muted rounded-lg"></div>
        </div>
      </div>

      {/* Category Chart */}
      <div className="bg-card rounded-lg border border-border p-6">
        <div className="h-6 bg-muted rounded w-48 mb-4"></div>
        <div className="h-80 bg-muted rounded"></div>
      </div>

      {/* Severity Chart */}
      <div className="bg-card rounded-lg border border-border p-6">
        <div className="h-6 bg-muted rounded w-48 mb-4"></div>
        <div className="h-80 bg-muted rounded"></div>
      </div>
    </div>
  );
}
