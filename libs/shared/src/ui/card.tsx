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
