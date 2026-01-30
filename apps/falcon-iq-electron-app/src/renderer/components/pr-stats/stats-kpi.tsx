import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts';

interface StatsKPIProps {
  label: string;
  value: number;
  icon: 'target' | 'search';
  color: 'primary' | 'warning';
}

export function StatsKPI({ label, value, icon, color }: StatsKPIProps) {
  // Prepare data for radial chart
  const data = [{ value, fill: color === 'primary' ? '#6366f1' : '#f59e0b' }];

  const iconSvg = icon === 'target' ? (
    <svg
      className="w-5 h-5"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  ) : (
    <svg
      className="w-5 h-5"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
      />
    </svg>
  );

  return (
    <div className="relative p-6 bg-card rounded-lg border border-border">
      <div className="flex items-center gap-3 mb-2">
        <div className={`${color === 'primary' ? 'text-primary' : 'text-warning'}`}>
          {iconSvg}
        </div>
        <h4 className="text-sm font-medium text-muted-foreground">{label}</h4>
      </div>
      <div className="flex items-center justify-between">
        <div className="text-3xl font-bold text-foreground">{value.toFixed(1)}%</div>
        <div className="w-20 h-20">
          <ResponsiveContainer width="100%" height="100%">
            <RadialBarChart
              cx="50%"
              cy="50%"
              innerRadius="70%"
              outerRadius="100%"
              barSize={8}
              data={data}
              startAngle={90}
              endAngle={-270}
            >
              <RadialBar
                background={{ fill: 'var(--color-muted)' }}
                dataKey="value"
                cornerRadius={10}
              />
            </RadialBarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
