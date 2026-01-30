export function EmptyState() {
  return (
    <div className="bg-card rounded-lg border border-border p-12 text-center">
      <svg
        className="mx-auto h-16 w-16 text-muted-foreground mb-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
      <h3 className="text-lg font-semibold text-foreground mb-2">
        No PR Comment Data Available
      </h3>
      <p className="text-muted-foreground max-w-sm mx-auto">
        This user doesn't have any PR comment analysis data yet. Data will appear here once
        PR comments are analyzed.
      </p>
    </div>
  );
}
