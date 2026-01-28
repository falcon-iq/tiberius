import { type ReactNode } from 'react';

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

// Helper function to generate initials
function getInitials(user: { firstname?: string | null; lastname?: string | null; username: string }): string {
  // Priority 1: Use firstname + lastname
  if (user.firstname && user.lastname) {
    return (user.firstname[0] + user.lastname[0]).toUpperCase();
  }

  // Priority 2: Use firstname only (take first two letters)
  if (user.firstname && user.firstname.length >= 2) {
    return user.firstname.slice(0, 2).toUpperCase();
  }

  // Priority 3: Use lastname only (take first two letters)
  if (user.lastname && user.lastname.length >= 2) {
    return user.lastname.slice(0, 2).toUpperCase();
  }

  // Priority 4: Fallback to username (take first two letters, strip EMU suffix)
  const usernameWithoutSuffix = user.username.includes('_')
    ? user.username.slice(0, user.username.lastIndexOf('_'))
    : user.username;

  return usernameWithoutSuffix.slice(0, 2).toUpperCase();
}

// Helper function to generate display name
function getDisplayName(user: { firstname?: string | null; lastname?: string | null; username: string }): string {
  // Priority 1: "Firstname Lastname"
  if (user.firstname && user.lastname) {
    return `${user.firstname} ${user.lastname}`;
  }

  // Priority 2: Just firstname
  if (user.firstname) {
    return user.firstname;
  }

  // Priority 3: Just lastname
  if (user.lastname) {
    return user.lastname;
  }

  // Priority 4: Fallback to username (stripped of EMU suffix)
  if (user.username.includes('_')) {
    return user.username.slice(0, user.username.lastIndexOf('_'));
  }

  return user.username;
}
