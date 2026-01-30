import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface CategoryStat {
  category: string;
  count: number;
  percentage: number;
}

interface CategoryDistributionProps {
  data: CategoryStat[];
}

// Use CSS variables for theming consistency
const COLORS = [
  'hsl(var(--color-primary))',
  'hsl(262 83% 58%)', // purple
  'hsl(330 81% 60%)', // pink
  'hsl(38 92% 50%)', // amber
  'hsl(160 84% 39%)', // emerald
  'hsl(217 91% 60%)', // blue
  'hsl(0 84% 60%)', // red
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
    <div className="w-full h-80" role="img" aria-label="Category distribution chart showing comment counts by category">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={topCategories}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 150, bottom: 5 }}
          accessibilityLayer
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
