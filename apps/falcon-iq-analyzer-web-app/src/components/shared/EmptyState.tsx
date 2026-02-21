interface EmptyStateProps {
  icon?: string;
  title: string;
  message: string;
}

export function EmptyState({ icon = '🌐', title, message }: EmptyStateProps) {
  return (
    <div className="text-center py-12 px-6" style={{ color: '#b0b8d1' }}>
      <div className="text-5xl mb-3 opacity-50">{icon}</div>
      <div className="text-[15px] font-semibold" style={{ color: '#8890a4' }}>
        {title}
      </div>
      <div className="text-[13px] mt-1">{message}</div>
    </div>
  );
}
