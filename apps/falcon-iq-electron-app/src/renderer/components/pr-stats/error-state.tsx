interface ErrorStateProps {
  error: Error;
}

export function ErrorState({ error }: ErrorStateProps) {
  return (
    <div className="bg-card rounded-lg border border-destructive/50 p-12 text-center">
      <svg
        className="mx-auto h-16 w-16 text-destructive mb-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <h3 className="text-lg font-semibold text-foreground mb-2">
        Failed to Load PR Comment Statistics
      </h3>
      <p className="text-muted-foreground max-w-sm mx-auto mb-4">
        {error.message || 'An unexpected error occurred while loading the data.'}
      </p>
      <button
        onClick={() => window.location.reload()}
        className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
      >
        Retry
      </button>
    </div>
  );
}
