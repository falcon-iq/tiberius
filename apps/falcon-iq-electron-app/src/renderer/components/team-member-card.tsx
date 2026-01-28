import { Card } from '@libs/shared/ui/card';
import { getDisplayName, getInitials } from '@libs/shared/utils/user-display';

export interface TeamMemberCardProps {
  user: {
    username: string;
    firstname?: string | null;
    lastname?: string | null;
    github_suffix?: string | null;
  };
  onClick?: () => void;
}

export function TeamMemberCard({ user, onClick }: TeamMemberCardProps) {
  const initials = getInitials(user);
  const displayName = getDisplayName(user);

  return (
    <Card
      className="flex items-center gap-4 p-4"
      onClick={onClick}
    >
      {/* Initials Circle */}
      <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
        <span className="text-sm font-semibold">{initials}</span>
      </div>

      {/* Name */}
      <div className="flex-1">
        <p className="text-sm font-medium text-card-foreground">{displayName}</p>
      </div>
    </Card>
  );
}
