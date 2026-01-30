export function LoadingSkeleton() {
  return (
    <div className="bg-card rounded-lg border border-border p-6">
      {/* Header skeleton */}
      <div className="mb-6">
        <div className="h-7 w-48 bg-muted rounded animate-pulse mb-2" />
        <div className="h-4 w-64 bg-muted rounded animate-pulse" />
      </div>

      {/* Card grid skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className="flex items-center gap-4 p-5 border border-border rounded-lg animate-pulse"
          >
            <div className="w-12 h-12 rounded-full bg-muted" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-32 bg-muted rounded" />
              <div className="h-3 w-24 bg-muted rounded" />
            </div>
            <div className="w-16 h-8 bg-muted rounded" />
          </div>
        ))}

        {/* System-level concerns skeleton */}
        <div className="md:col-span-2">
          <div className="border border-border rounded-lg overflow-hidden animate-pulse">
            <div className="flex items-center gap-4 p-5">
              <div className="w-12 h-12 rounded-full bg-muted" />
              <div className="flex-1 space-y-2">
                <div className="h-4 w-48 bg-muted rounded" />
                <div className="h-3 w-36 bg-muted rounded" />
              </div>
              <div className="w-16 h-8 bg-muted rounded" />
              <div className="w-5 h-5 bg-muted rounded" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
