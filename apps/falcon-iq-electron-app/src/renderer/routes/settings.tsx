import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/settings')({
  component: Settings,
});

function Settings() {
  return (
    <div className="min-h-screen bg-background text-foreground p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-4xl font-bold mb-6">Settings</h1>
        <div className="space-y-6">
          <div className="bg-card p-6 rounded-lg border border-border">
            <h2 className="text-xl font-semibold mb-3">Appearance</h2>
            <p className="text-muted-foreground">
              Configure your theme and display preferences.
            </p>
          </div>
          <div className="bg-card p-6 rounded-lg border border-border">
            <h2 className="text-xl font-semibold mb-3">General</h2>
            <p className="text-muted-foreground">
              Manage general application settings.
            </p>
          </div>
          <div className="mt-8">
            <a
              href="/"
              className="text-primary hover:underline"
            >
              ← Back to Home
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

