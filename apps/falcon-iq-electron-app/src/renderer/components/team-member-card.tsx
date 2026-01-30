import { Card } from '@libs/shared/ui/card';
import { getDisplayName, getInitials } from '@libs/shared/utils/user-display';
import { useState } from 'react';

export interface TeamMemberCardProps {
  user: {
    username: string;
    firstname?: string | null;
    lastname?: string | null;
    github_suffix?: string | null;
    avatar_url?: string | null;
  };
  onClick?: () => void;
}

export function TeamMemberCard({ user, onClick }: TeamMemberCardProps) {
  const initials = getInitials(user);
  const displayName = getDisplayName(user);
  const [imageError, setImageError] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);

  // Show avatar if URL exists and hasn't errored
  const shouldShowAvatar = user.avatar_url && !imageError;

  return (
    <Card
      className="flex items-center gap-4 p-4"
      onClick={onClick}
    >
      {/* Avatar or Initials Circle */}
      <div className="relative flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground overflow-hidden">
        {shouldShowAvatar ? (
          <>
            {/* Initials shown while loading */}
            <span
              className={`text-sm font-semibold transition-opacity ${
                imageLoaded ? 'opacity-0' : 'opacity-100'
              }`}
            >
              {initials}
            </span>

            {/* Avatar image */}
            <img
              src={user.avatar_url || ''}
              alt={displayName}
              className={`absolute inset-0 h-full w-full object-cover transition-opacity ${
                imageLoaded ? 'opacity-100' : 'opacity-0'
              }`}
              onLoad={() => setImageLoaded(true)}
              onError={() => {
                setImageError(true);
                setImageLoaded(false);
              }}
            />
          </>
        ) : (
          /* No avatar - show initials */
          <span className="text-sm font-semibold">{initials}</span>
        )}
      </div>

      {/* Name */}
      <div className="flex-1">
        <p className="text-sm font-medium text-card-foreground">{displayName}</p>
      </div>
    </Card>
  );
}
