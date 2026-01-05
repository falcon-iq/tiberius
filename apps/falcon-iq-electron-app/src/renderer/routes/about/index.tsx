import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/about/')({
  component: About,
});

function About() {
  return (
    <div className="min-h-screen bg-background text-foreground p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-4xl font-bold mb-6">About Amista</h1>
        <div className="space-y-4 text-lg">
          <p>
            Amista is a modern Electron application built with cutting-edge web
            technologies.
          </p>
          <p className="text-muted-foreground">
            This application demonstrates the power of combining Electron with
            React, TanStack Router, and Tailwind CSS to create beautiful,
            performant desktop applications.
          </p>
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

