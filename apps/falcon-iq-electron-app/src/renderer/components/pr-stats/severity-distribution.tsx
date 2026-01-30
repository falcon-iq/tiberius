import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface SeverityStat {
  severity: string;
  count: number;
  percentage: number;
}

interface SeverityDistributionProps {
  data: SeverityStat[];
}

// Use CSS variables and HSL for theming consistency
const SEVERITY_COLORS: Record<string, string> = {
  TRIVIAL: 'hsl(160 84% 39%)', // emerald
  LOW: 'hsl(217 91% 60%)', // blue
  MEDIUM: 'hsl(38 92% 50%)', // amber
  HIGH: 'hsl(25 95% 53%)', // orange
  BLOCKER: 'hsl(0 84% 60%)', // red
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
    <div className="w-full h-80" role="img" aria-label="Severity distribution chart showing comment counts by severity level">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          accessibilityLayer
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
                fill={SEVERITY_COLORS[entry.severity] || 'hsl(var(--color-primary))'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
