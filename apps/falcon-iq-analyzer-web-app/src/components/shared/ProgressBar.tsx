interface ProgressBarProps {
  pct: number;
  message?: string;
}

export function ProgressBar({ pct, message }: ProgressBarProps) {
  return (
    <div>
      <div className="bg-[#e9ecef] rounded-full h-2 overflow-hidden my-3">
        <div
          className="bg-[#4a6cf7] h-full rounded-full transition-all duration-300"
          style={{ width: `${Math.max(0, Math.min(100, pct))}%` }}
        />
      </div>
      {message && (
        <p className="text-[13px] text-[#666] mt-2 flex items-center gap-2">
          <span className="spinner-icon" />
          {message}
        </p>
      )}
    </div>
  );
}
