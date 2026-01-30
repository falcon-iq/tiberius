import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface SeverityStat {
  severity: string;
  count: number;
  percentage: number;
}

interface SeverityDistributionProps {
  data: SeverityStat[];
}

const SEVERITY_COLORS: Record<string, string> = {
  TRIVIAL: '#10b981', // green-500
  LOW: '#3b82f6', // blue-500
  MEDIUM: '#f59e0b', // yellow-500
  HIGH: '#f97316', // orange-500
  BLOCKER: '#ef4444', // red-500
};

export function SeverityDistribution({ data }: SeverityDistributionProps) {
  if (data.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-8">
        No severity data available
      </div>
    );
  }

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
          <XAxis
            dataKey="severity"
            stroke="var(--color-muted-foreground)"
            tick={{ fill: 'var(--color-foreground)', fontSize: 12 }}
          />
          <YAxis stroke="var(--color-muted-foreground)" />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--color-card)',
              border: '1px solid var(--color-border)',
              borderRadius: '0.5rem',
              color: 'var(--color-foreground)',
            }}
            formatter={(value: number) => [value, 'Count']}
            labelFormatter={(label: string) => {
              const item = data.find(s => s.severity === label);
              return item ? `${label} (${item.percentage}%)` : label;
            }}
          />
          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={SEVERITY_COLORS[entry.severity] || '#6366f1'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
