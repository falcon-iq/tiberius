import { type ReactNode } from 'react';
import { getDisplayName, getInitials } from '../../utils/user-display';

// Generic Card Component
export interface CardProps {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
}

export function Card({ children, className = '', onClick }: CardProps) {
  return (
    <div
      className={[
        'rounded-lg border border-border bg-card p-6',
        onClick ? 'cursor-pointer transition-colors hover:bg-accent' : '',
        className
      ].filter(Boolean).join(' ')}
      onClick={onClick}
    >
      {children}
    </div>
  );
}

// TeamMemberCard - Specialized card for user display
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
