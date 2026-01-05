import { createFileRoute } from '@tanstack/react-router';

const Index = () => {
  return (
    <>
      {/* Header */}
      <header className="flex h-16 items-center border-b border-border bg-card px-6">
        <h1 className="text-xl font-semibold text-foreground">Manager Dashboard</h1>
      </header>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-7xl space-y-6">
          {/* Placeholder content */}
          <div className="rounded-lg border border-border bg-card p-6">
            <h2 className="mb-2 text-lg font-medium text-foreground">Welcome to Manager Buddy</h2>
            <p className="text-sm text-muted-foreground">
              Your main work area will be displayed here. This is where dashboards, team views, and detailed information
              will appear.
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="rounded-lg border border-border bg-card p-6">
              <h3 className="mb-2 font-medium text-foreground">Component Area 1</h3>
              <p className="text-sm text-muted-foreground">Content will be displayed here</p>
            </div>

            <div className="rounded-lg border border-border bg-card p-6">
              <h3 className="mb-2 font-medium text-foreground">Component Area 2</h3>
              <p className="text-sm text-muted-foreground">Content will be displayed here</p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export const Route = createFileRoute('/')({
  component: Index,
});
