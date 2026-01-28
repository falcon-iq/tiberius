import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { TeamMemberCard } from '@components/team-member-card';
import { useUsers } from '@hooks/use-users';
import { Loader2 } from 'lucide-react';

const Index = () => {
  const { data: users, isLoading, error } = useUsers();
  const navigate = useNavigate();

  return (
    <>
      {/* Header */}
      <header className="flex h-16 items-center border-b border-border bg-card px-6">
        <h1 className="text-xl font-semibold text-foreground">Manager Dashboard</h1>
      </header>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-7xl space-y-6">
          {/* Team Members Section */}
          <div>
            <h2 className="mb-4 text-lg font-medium text-foreground">Team Members</h2>

            {/* Loading State */}
            {isLoading && (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
                <p className="text-sm text-destructive">
                  Failed to load team members. Please try again.
                </p>
              </div>
            )}

            {/* Empty State */}
            {!isLoading && !error && (!users || users.length === 0) && (
              <div className="rounded-lg border border-border bg-card p-12 text-center">
                <p className="text-sm text-muted-foreground">
                  No team members added yet. Add team members in Settings.
                </p>
              </div>
            )}

            {/* Team Member Cards Grid */}
            {!isLoading && !error && users && users.length > 0 && (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {users.map((user) => (
                  <TeamMemberCard
                    key={user.id}
                    user={user}
                    onClick={() => {
                      void navigate({ to: '/users/$id', params: { id: String(user.id) } });
                    }}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export const Route = createFileRoute('/')({
  component: Index,
});
