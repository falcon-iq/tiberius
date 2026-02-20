import type { SiteStatus } from '@app-types/api';

interface StatusConfig {
  bg: string;
  text: string;
  dot: string;
  pulse: boolean;
}

const STATUS_CONFIG: Record<SiteStatus, StatusConfig> = {
  pending: { bg: '#f3f4f6', text: '#6b7280', dot: '#9ca3af', pulse: false },
  crawling: { bg: '#dbeafe', text: '#1d4ed8', dot: '#3b82f6', pulse: true },
  crawled: { bg: '#dcfce7', text: '#15803d', dot: '#22c55e', pulse: false },
  analyzing: { bg: '#fef3c7', text: '#a16207', dot: '#f59e0b', pulse: true },
  analyzed: { bg: '#ccfbf1', text: '#0d9488', dot: '#14b8a6', pulse: false },
  failed: { bg: '#fee2e2', text: '#dc2626', dot: '#ef4444', pulse: false },
};

interface StatusBadgeProps {
  status: SiteStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status];
  return (
    <span
      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wide"
      style={{ backgroundColor: config.bg, color: config.text }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full flex-shrink-0"
        style={{
          backgroundColor: config.dot,
          animation: config.pulse ? 'pulse-dot 1.5s infinite' : 'none',
        }}
      />
      {status}
    </span>
  );
}
