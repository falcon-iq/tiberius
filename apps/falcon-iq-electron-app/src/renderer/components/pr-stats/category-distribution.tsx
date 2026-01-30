import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface CategoryStat {
  category: string;
  count: number;
  percentage: number;
}

interface CategoryDistributionProps {
  data: CategoryStat[];
}

const COLORS = [
  '#6366f1', // primary
  '#8b5cf6', // purple
  '#ec4899', // pink
  '#f59e0b', // amber
  '#10b981', // emerald
  '#3b82f6', // blue
  '#ef4444', // red
];

export function CategoryDistribution({ data }: CategoryDistributionProps) {
  // Show top 7 categories only
  const topCategories = data.slice(0, 7);

  if (topCategories.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-8">
        No category data available
      </div>
    );
  }

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={topCategories}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 150, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
          <XAxis type="number" stroke="var(--color-muted-foreground)" />
          <YAxis
            type="category"
            dataKey="category"
            width={140}
            stroke="var(--color-muted-foreground)"
            tick={{ fill: 'var(--color-foreground)', fontSize: 12 }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--color-card)',
              border: '1px solid var(--color-border)',
              borderRadius: '0.5rem',
              color: 'var(--color-foreground)',
            }}
            formatter={(value: number) => [value, 'Count']}
            labelFormatter={(label: string) => {
              const item = topCategories.find(c => c.category === label);
              return item ? `${label} (${item.percentage}%)` : label;
            }}
          />
          <Bar dataKey="count" radius={[0, 4, 4, 0]}>
            {topCategories.map((_, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
