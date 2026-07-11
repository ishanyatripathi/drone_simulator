interface StatBarProps {
  label: string;
  value: number; // 0-100
  displayValue: string;
  colorClass?: string;
}

export function StatBar({ label, value, displayValue, colorClass = 'bg-aeris-cyan' }: StatBarProps) {
  return (
    <div className="flex flex-col gap-1 min-w-[110px]">
      <div className="flex items-center justify-between">
        <span className="hud-label">{label}</span>
        <span className="hud-value text-xs">{displayValue}</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-white/5 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${colorClass}`}
          style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
        />
      </div>
    </div>
  );
}
