import { createFileRoute, Link, useNavigate } from '@tanstack/react-router';
import { useUsers } from '@hooks/use-users';
import { Loader2, ArrowLeft } from 'lucide-react';
import { useEffect } from 'react';
import { getDisplayName, getInitials } from '@libs/shared/lib/user-display';

export const Route = createFileRoute('/users/$id')({
  component: UserDetail,
});

function UserDetail() {
  const { id } = Route.useParams();
  const navigate = useNavigate();
  const { data: users, isLoading, error } = useUsers();

  // Parse and validate ID
  const userId = parseInt(id, 10);
  const isValidId = !isNaN(userId);
  const user = users?.find((u) => u.id === userId);

  // Redirect if user not found
  useEffect(() => {
    if (!isLoading && !error && isValidId && !user) {
      void navigate({ to: '/' });
    }
  }, [isLoading, error, isValidId, user, navigate]);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <>
        <header className="flex h-16 items-center gap-4 border-b border-border bg-card px-6">
          <Link
            to="/"
            className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </Link>
        </header>
        <div className="flex-1 overflow-y-auto p-6">
          <div className="mx-auto max-w-3xl">
            <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
              <p className="text-sm text-destructive">
                Failed to load user details. Please try again.
              </p>
            </div>
          </div>
        </div>
      </>
    );
  }

  // Invalid ID
  if (!isValidId) {
    return (
      <>
        <header className="flex h-16 items-center gap-4 border-b border-border bg-card px-6">
          <Link
            to="/"
            className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </Link>
        </header>
        <div className="flex-1 overflow-y-auto p-6">
          <div className="mx-auto max-w-3xl">
            <div className="rounded-lg border border-border bg-card p-12 text-center">
              <p className="text-sm text-muted-foreground">Invalid user ID</p>
            </div>
          </div>
        </div>
      </>
    );
  }

  // User not found (will redirect)
  if (!user) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // Display user
  const displayName = getDisplayName(user);
  const initials = getInitials(user);

  return (
    <>
      <header className="flex h-16 items-center gap-4 border-b border-border bg-card px-6">
        <Link
          to="/"
          className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Link>
        <h1 className="text-xl font-semibold text-foreground">Team Member Details</h1>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-3xl space-y-6">
          <div className="rounded-lg border border-border bg-card p-6">
            <div className="flex items-center gap-6">
              <div className="flex h-20 w-20 flex-shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                <span className="text-2xl font-semibold">{initials}</span>
              </div>

              <div className="flex-1">
                <h2 className="text-2xl font-semibold text-card-foreground">
                  {displayName}
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">@{user.username}</p>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-card p-6">
            <p className="text-sm text-muted-foreground">
              Additional details coming soon...
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
